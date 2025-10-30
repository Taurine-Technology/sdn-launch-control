from typing import List, Tuple

from django.core.management.base import BaseCommand, CommandParser
from django.db import connection


SECTIONS = (
    'rss',
    'workers',
    'latency',
    'latency_cagg',
    'pool',
    'channels',
    'celery',
    'overview',
)


class Command(BaseCommand):
    help = "Observability report: query telemetry.* for quick diagnostics"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--section', choices=SECTIONS, default='overview',
            help='Which report to run'
        )
        parser.add_argument(
            '--window', default='24 hours',
            help="Time window, e.g. '6 hours', '1 day', '90 minutes'"
        )

    def handle(self, *args, **options):
        section = options['section']
        window = options['window']
        if section == 'overview':
            self._print("RSS (5m buckets)")
            self._run_sql(self._sql_rss_bucketed(window))
            self.stdout.write("")
            self._print("Worker events")
            self._run_sql(self._sql_workers(window))
            self.stdout.write("")
            self._print("API latency (raw, last hour shown if window > 1h)")
            lat_window = '1 hour' if _duration_gt_hour(window) else window
            self._run_sql(self._sql_latency_raw(lat_window))
            return

        sql = self._dispatch_sql(section, window)
        self._run_sql(sql)

    def _dispatch_sql(self, section: str, window: str) -> str:
        if section == 'rss':
            return self._sql_rss(window)
        if section == 'workers':
            return self._sql_workers(window)
        if section == 'latency':
            return self._sql_latency_raw(window)
        if section == 'latency_cagg':
            return self._sql_latency_cagg(window)
        if section == 'pool':
            return self._sql_pool(window)
        if section == 'channels':
            return self._sql_channels(window)
        if section == 'celery':
            return self._sql_celery(window)
        raise ValueError(f"Unknown section {section}")

    def _run_sql(self, sql: str) -> None:
        with connection.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
        self._print_table(cols, rows)

    def _print(self, title: str) -> None:
        self.stdout.write(title)
        self.stdout.write('-' * len(title))

    def _print_table(self, headers: List[str], rows: List[Tuple]) -> None:
        # Minimal fixed-width renderer
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(str(cell)))
        fmt = '  '.join('{:%d}' % w for w in widths)
        self.stdout.write(fmt.format(*headers))
        self.stdout.write(fmt.format(*['-' * w for w in widths]))
        for row in rows[:1000]:
            self.stdout.write(fmt.format(*[str(c) for c in row]))

    # SQL helpers
    def _sql_rss(self, window: str) -> str:
        return f"""
        SELECT ts, rss_mb
        FROM telemetry.api_process_gauges
        WHERE ts > now() - interval '{window}'
        ORDER BY ts
        """

    def _sql_rss_bucketed(self, window: str) -> str:
        return f"""
        SELECT time_bucket('5 minutes', ts) AS bucket, avg(rss_mb) AS rss_avg_mb
        FROM telemetry.api_process_gauges
        WHERE ts > now() - interval '{window}'
        GROUP BY bucket
        ORDER BY bucket
        """

    def _sql_workers(self, window: str) -> str:
        return f"""
        SELECT ts, event, worker_pid
        FROM telemetry.gunicorn_events
        WHERE ts > now() - interval '{window}'
        ORDER BY ts
        """

    def _sql_latency_raw(self, window: str) -> str:
        return f"""
        SELECT date_trunc('minute', ts) AS minute,
               count(*) AS reqs,
               percentile_cont(0.9) WITHIN GROUP (ORDER BY dur_ms) AS p90_ms,
               percentile_cont(0.99) WITHIN GROUP (ORDER BY dur_ms) AS p99_ms
        FROM telemetry.api_requests
        WHERE ts > now() - interval '{window}'
        GROUP BY 1
        ORDER BY 1
        """

    def _sql_latency_cagg(self, window: str) -> str:
        return f"""
        SELECT bucket, route, method, status, reqs, p90, p99
        FROM telemetry.api_requests_1m
        WHERE bucket > now() - interval '{window}'
        ORDER BY bucket
        """

    def _sql_pool(self, window: str) -> str:
        return f"""
        SELECT ts, size, checked_in, checked_out, overflow
        FROM telemetry.db_pool_stats
        WHERE ts > now() - interval '{window}'
        ORDER BY ts
        """

    def _sql_channels(self, window: str) -> str:
        return f"""
        SELECT ts, conns, groups, msgs_per_s
        FROM telemetry.channels_stats
        WHERE ts > now() - interval '{window}'
        ORDER BY ts
        """

    def _sql_celery(self, window: str) -> str:
        return f"""
        SELECT ts, task, status, dur_ms, rss_after_mb
        FROM telemetry.celery_tasks
        WHERE ts > now() - interval '{window}'
        ORDER BY ts DESC
        LIMIT 500
        """


def _duration_gt_hour(window: str) -> bool:
    try:
        w = window.strip().lower()
        return ('day' in w) or (w.endswith('hours') and int(w.split()[0]) > 1) or (w.endswith('hour') and int(w.split()[0]) > 1)
    except Exception:
        return False



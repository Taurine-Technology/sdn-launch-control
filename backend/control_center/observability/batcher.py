import os
import threading
import time
import logging
from collections import deque
from typing import Deque, Dict, List, Tuple

from django.db import connections, DEFAULT_DB_ALIAS
from django.db.utils import OperationalError


class _InsertBatcher:
    def __init__(
        self,
        table: str,
        columns: Tuple[str, ...],
        maxlen: int = 5000,
        batch_size: int = 400,
        interval_s: float = 1.0,
    ):
        self.table = table
        self.columns = columns
        self.queue: Deque[Tuple] = deque(maxlen=maxlen)
        self.batch_size = batch_size
        self.interval_s = interval_s
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name=f"obs-batcher-{table}", daemon=True)
        self._logger = logging.getLogger(__name__)
        self._logger.info("Created InsertBatcher for table=%s columns=%s batch_size=%d interval_s=%.2f", table, columns, batch_size, interval_s)

    def start(self):
        if not self._thread.is_alive():
            self._thread.start()
            self._logger.info("Started InsertBatcher thread for table=%s", self.table)

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2)
        self._logger.info("Stopped InsertBatcher thread for table=%s", self.table)

    def put(self, row: Tuple):
        # Drop-oldest behavior via deque(maxlen)
        self.queue.append(row)
        # Use debug to avoid log spam under load
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug("Queued row for table=%s; queue_len=%d", self.table, len(self.queue))

    def _flush(self, rows: List[Tuple]):
        if not rows:
            return
        sql_cols = ",".join(self.columns)
        placeholders = ",".join(["%s"] * len(self.columns))
        sql = f"INSERT INTO {self.table} ({sql_cols}) VALUES ({placeholders})"
        try:
            conn = connections[DEFAULT_DB_ALIAS]
            with conn.cursor() as cur:
                cur.executemany(sql, rows)
            self._logger.debug("Flushed %d rows into %s", len(rows), self.table)
        except OperationalError:
            # Transient failure; drop batch to avoid blocking hot path
            self._logger.warning("OperationalError flushing %d rows into %s; dropping batch", len(rows), self.table, exc_info=True)
        except Exception:
            # Any other error should be visible but non-fatal
            self._logger.error("Unexpected error flushing %d rows into %s; dropping batch", len(rows), self.table, exc_info=True)

    def _run(self):
        while not self._stop.is_set():
            time.sleep(self.interval_s)
            rows: List[Tuple] = []
            while self.queue and len(rows) < self.batch_size:
                rows.append(self.queue.popleft())
            self._flush(rows)


_batchers: Dict[str, _InsertBatcher] = {}


def get_batcher(table: str, columns: Tuple[str, ...]) -> _InsertBatcher:
    key = f"{table}:{','.join(columns)}"
    batcher = _batchers.get(key)
    if batcher is None:
        batcher = _InsertBatcher(table=table, columns=columns)
        _batchers[key] = batcher
    return batcher


def start_default_batchers_if_enabled():
    if os.environ.get("OBS_ENABLE", "true").lower() != "true":
        return
    # Start batchers for all known telemetry tables so producers can enqueue safely
    get_batcher(
        table="telemetry.api_requests",
        columns=("ts", "route", "method", "status", "bytes", "dur_ms", "host"),
    ).start()
    get_batcher(
        table="telemetry.api_process_gauges",
        columns=("ts", "rss_mb", "heap_mb", "gc_gen0", "gc_gen1", "gc_gen2", "threads", "fds"),
    ).start()
    get_batcher(
        table="telemetry.db_pool_stats",
        columns=("ts", "size", "checked_in", "checked_out", "overflow"),
    ).start()
    get_batcher(
        table="telemetry.channels_stats",
        columns=("ts", "conns", "groups", "msgs_per_s"),
    ).start()
    get_batcher(
        table="telemetry.celery_tasks",
        columns=("ts", "task", "status", "dur_ms", "rss_before_mb", "rss_after_mb"),
    ).start()
    get_batcher(
        table="telemetry.gunicorn_events",
        columns=("ts", "event", "worker_pid"),
    ).start()



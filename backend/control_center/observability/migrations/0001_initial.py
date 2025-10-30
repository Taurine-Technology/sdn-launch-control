from django.db import migrations


CREATE_SQL = r'''
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE SCHEMA IF NOT EXISTS telemetry;

-- api_requests
CREATE TABLE IF NOT EXISTS telemetry.api_requests (
  ts timestamptz NOT NULL,
  route text NOT NULL,
  method text NOT NULL,
  status integer NOT NULL,
  bytes bigint NOT NULL,
  dur_ms double precision NOT NULL,
  host text NOT NULL
);
SELECT public.create_hypertable('telemetry.api_requests','ts', if_not_exists=>TRUE);

-- api_process_gauges
CREATE TABLE IF NOT EXISTS telemetry.api_process_gauges (
  ts timestamptz NOT NULL,
  rss_mb double precision NOT NULL,
  heap_mb double precision NOT NULL,
  gc_gen0 integer NOT NULL,
  gc_gen1 integer NOT NULL,
  gc_gen2 integer NOT NULL,
  threads integer NOT NULL,
  fds integer NOT NULL
);
SELECT public.create_hypertable('telemetry.api_process_gauges','ts', if_not_exists=>TRUE);

-- celery_tasks
CREATE TABLE IF NOT EXISTS telemetry.celery_tasks (
  ts timestamptz NOT NULL,
  task text NOT NULL,
  status text NOT NULL,
  dur_ms double precision NOT NULL,
  rss_before_mb double precision NULL,
  rss_after_mb double precision NULL
);
SELECT public.create_hypertable('telemetry.celery_tasks','ts', if_not_exists=>TRUE);

-- channels_stats
CREATE TABLE IF NOT EXISTS telemetry.channels_stats (
  ts timestamptz NOT NULL,
  conns integer NOT NULL,
  groups integer NOT NULL,
  msgs_per_s double precision NOT NULL
);
SELECT public.create_hypertable('telemetry.channels_stats','ts', if_not_exists=>TRUE);

-- gunicorn_events
CREATE TABLE IF NOT EXISTS telemetry.gunicorn_events (
  ts timestamptz NOT NULL,
  event text NOT NULL,
  worker_pid integer NOT NULL
);
SELECT public.create_hypertable('telemetry.gunicorn_events','ts', if_not_exists=>TRUE);

-- db_pool_stats
CREATE TABLE IF NOT EXISTS telemetry.db_pool_stats (
  ts timestamptz NOT NULL,
  size integer NOT NULL,
  checked_in integer NOT NULL,
  checked_out integer NOT NULL,
  overflow integer NOT NULL
);
SELECT public.create_hypertable('telemetry.db_pool_stats','ts', if_not_exists=>TRUE);

-- retention policies (14d raw)
SELECT add_retention_policy('telemetry.api_requests', INTERVAL '14 days');
SELECT add_retention_policy('telemetry.api_process_gauges', INTERVAL '14 days');
SELECT add_retention_policy('telemetry.celery_tasks', INTERVAL '14 days');
SELECT add_retention_policy('telemetry.channels_stats', INTERVAL '14 days');
SELECT add_retention_policy('telemetry.gunicorn_events', INTERVAL '14 days');
SELECT add_retention_policy('telemetry.db_pool_stats', INTERVAL '14 days');

-- continuous aggregates (1 minute), keep 90d
CREATE MATERIALIZED VIEW IF NOT EXISTS telemetry.api_requests_1m
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 minute', ts) AS bucket,
       route,
       method,
       status,
       count(*) AS reqs,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY dur_ms) AS p50,
       percentile_cont(0.9) WITHIN GROUP (ORDER BY dur_ms) AS p90,
       percentile_cont(0.99) WITHIN GROUP (ORDER BY dur_ms) AS p99
FROM telemetry.api_requests
GROUP BY bucket, route, method, status
WITH NO DATA;
SELECT add_continuous_aggregate_policy('telemetry.api_requests_1m',
    start_offset => INTERVAL '7 days',
    end_offset   => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute');
SELECT add_retention_policy('telemetry.api_requests_1m', INTERVAL '90 days');
'''


DROP_SQL = r'''
DROP MATERIALIZED VIEW IF EXISTS telemetry.api_requests_1m;
DROP TABLE IF EXISTS telemetry.db_pool_stats;
DROP TABLE IF EXISTS telemetry.gunicorn_events;
DROP TABLE IF EXISTS telemetry.channels_stats;
DROP TABLE IF EXISTS telemetry.celery_tasks;
DROP TABLE IF EXISTS telemetry.api_process_gauges;
DROP TABLE IF EXISTS telemetry.api_requests;
-- keep schema in place
'''


class Migration(migrations.Migration):
    initial = True
    atomic = False

    dependencies = []

    operations = [
        migrations.RunSQL(sql=CREATE_SQL, reverse_sql=DROP_SQL),
    ]



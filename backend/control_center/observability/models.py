from django.db import models


class ApiRequest(models.Model):
    ts = models.DateTimeField()
    route = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    status = models.IntegerField()
    bytes = models.BigIntegerField()
    dur_ms = models.FloatField()
    host = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'telemetry.api_requests'


class ApiProcessGauges(models.Model):
    ts = models.DateTimeField()
    rss_mb = models.FloatField()
    heap_mb = models.FloatField()
    gc_gen0 = models.IntegerField()
    gc_gen1 = models.IntegerField()
    gc_gen2 = models.IntegerField()
    threads = models.IntegerField()
    fds = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'telemetry.api_process_gauges'


class CeleryTaskMetric(models.Model):
    ts = models.DateTimeField()
    task = models.CharField(max_length=255)
    status = models.CharField(max_length=32)
    dur_ms = models.FloatField()
    rss_before_mb = models.FloatField(null=True)
    rss_after_mb = models.FloatField(null=True)

    class Meta:
        managed = False
        db_table = 'telemetry.celery_tasks'


class ChannelsStats(models.Model):
    ts = models.DateTimeField()
    conns = models.IntegerField()
    groups = models.IntegerField()
    msgs_per_s = models.FloatField()

    class Meta:
        managed = False
        db_table = 'telemetry.channels_stats'


class GunicornEvent(models.Model):
    ts = models.DateTimeField()
    event = models.CharField(max_length=64)
    worker_pid = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'telemetry.gunicorn_events'


class DbPoolStats(models.Model):
    ts = models.DateTimeField()
    size = models.IntegerField()
    checked_in = models.IntegerField()
    checked_out = models.IntegerField()
    overflow = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'telemetry.db_pool_stats'



# Migration to enable compression on DeviceStats hypertable

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('device_monitoring', '0003_make_devicestats_hypertable'),
    ]

    operations = [
        # Enable compression on DeviceStats hypertable
        migrations.RunSQL(
            sql="""
                ALTER TABLE device_monitoring_devicestats SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'ip_address',
                    timescaledb.compress_orderby = 'timestamp DESC'
                );
            """,
            reverse_sql="""
                ALTER TABLE device_monitoring_devicestats SET (timescaledb.compress = false);
            """
        ),
        
        # Add compression policy to compress chunks older than 1 day
        migrations.RunSQL(
            sql="""
                SELECT add_compression_policy(
                    'device_monitoring_devicestats',
                    INTERVAL '1 day',
                    if_not_exists => TRUE
                );
            """,
            reverse_sql="""
                SELECT remove_compression_policy('device_monitoring_devicestats', if_exists => TRUE);
            """
        ),
    ]


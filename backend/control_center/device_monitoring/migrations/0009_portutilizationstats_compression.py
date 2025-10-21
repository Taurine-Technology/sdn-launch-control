# Migration to enable compression on PortUtilizationStats hypertable

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('device_monitoring', '0008_make_portutilizationstats_hypertable'),
    ]

    operations = [
        # Enable compression on PortUtilizationStats hypertable
        migrations.RunSQL(
            sql="""
                ALTER TABLE device_monitoring_portutilizationstats SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'ip_address, port_name',
                    timescaledb.compress_orderby = 'timestamp DESC'
                );
            """,
            reverse_sql="""
                ALTER TABLE device_monitoring_portutilizationstats SET (timescaledb.compress = false);
            """
        ),
        
        # Add compression policy to compress chunks older than 6 hours
        # (keeps recent data uncompressed for fast per-second queries)
        migrations.RunSQL(
            sql="""
                SELECT add_compression_policy(
                    'device_monitoring_portutilizationstats',
                    INTERVAL '6 hours',
                    if_not_exists => TRUE
                );
            """,
            reverse_sql="""
                SELECT remove_compression_policy('device_monitoring_portutilizationstats', if_exists => TRUE);
            """
        ),
        
        # Add retention policy to drop chunks older than 90 days
        migrations.RunSQL(
            sql="""
                SELECT add_retention_policy(
                    'device_monitoring_portutilizationstats',
                    INTERVAL '90 days',
                    if_not_exists => TRUE
                );
            """,
            reverse_sql="""
                SELECT remove_retention_policy('device_monitoring_portutilizationstats', if_exists => TRUE);
            """
        ),
    ]

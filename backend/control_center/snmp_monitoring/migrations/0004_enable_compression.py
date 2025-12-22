# Migration to enable compression on SNMPMetrics and SNMPInterfaceStats hypertables

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('snmp_monitoring', '0003_make_hypertables'),
    ]

    operations = [
        # Enable compression on SNMPMetrics hypertable
        migrations.RunSQL(
            sql="""
                ALTER TABLE snmp_monitoring_snmpmetrics SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'device_id',
                    timescaledb.compress_orderby = 'timestamp DESC'
                );
            """,
            reverse_sql="""
                ALTER TABLE snmp_monitoring_snmpmetrics SET (timescaledb.compress = false);
            """
        ),

        # Add compression policy to compress chunks older than 1 day
        migrations.RunSQL(
            sql="""
                SELECT add_compression_policy(
                    'snmp_monitoring_snmpmetrics',
                    INTERVAL '1 day',
                    if_not_exists => TRUE
                );
            """,
            reverse_sql="""
                SELECT remove_compression_policy('snmp_monitoring_snmpmetrics', if_exists => TRUE);
            """
        ),

        # Enable compression on SNMPInterfaceStats hypertable
        migrations.RunSQL(
            sql="""
                ALTER TABLE snmp_monitoring_snmpinterfacestats SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'device_id, interface_name',
                    timescaledb.compress_orderby = 'timestamp DESC'
                );
            """,
            reverse_sql="""
                ALTER TABLE snmp_monitoring_snmpinterfacestats SET (timescaledb.compress = false);
            """
        ),

        # Add compression policy to compress chunks older than 6 hours
        # (keeps recent data uncompressed for fast per-second queries)
        migrations.RunSQL(
            sql="""
                SELECT add_compression_policy(
                    'snmp_monitoring_snmpinterfacestats',
                    INTERVAL '6 hours',
                    if_not_exists => TRUE
                );
            """,
            reverse_sql="""
                SELECT remove_compression_policy('snmp_monitoring_snmpinterfacestats', if_exists => TRUE);
            """
        ),
    ]

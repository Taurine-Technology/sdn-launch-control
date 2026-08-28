# Migration to convert SNMPMetrics and SNMPInterfaceStats to TimescaleDB hypertables

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False  # The hypertable conversion must run outside of a transaction.

    dependencies = [
        ('snmp_monitoring', '0002_alter_primary_keys'),
    ]

    operations = [
        # Ensure TimescaleDB extension exists before attempting hypertable operations
        migrations.RunSQL(
            sql="""
                CREATE EXTENSION IF NOT EXISTS timescaledb;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
        # Convert SNMPMetrics table to TimescaleDB hypertable
        # Note: create_default_indexes => FALSE prevents duplicate timestamp index
        # (migration 0001 already created all needed indexes including timestamp)
        # chunk_time_interval => '1 day' chosen for time-series data
        migrations.RunSQL(
            sql="""
                SELECT create_hypertable(
                    'snmp_monitoring_snmpmetrics',
                    'timestamp',
                    migrate_data => true,
                    if_not_exists => TRUE,
                    create_default_indexes => FALSE,
                    chunk_time_interval => INTERVAL '1 day'
                );
            """,
            reverse_sql="""
                -- Safely drop hypertable only if it exists and is actually a hypertable
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM timescaledb_information.hypertables
                        WHERE hypertable_name = 'snmp_monitoring_snmpmetrics'
                    ) THEN
                        PERFORM drop_hypertable('snmp_monitoring_snmpmetrics', IF_EXISTS => TRUE);
                    END IF;
                END $$;
            """
        ),
        # Convert SNMPInterfaceStats table to TimescaleDB hypertable
        # Note: create_default_indexes => FALSE prevents duplicate timestamp index
        # (migration 0001 already created all needed indexes including timestamp)
        # chunk_time_interval => '1 day' chosen for high-frequency data (stats every few seconds)
        migrations.RunSQL(
            sql="""
                SELECT create_hypertable(
                    'snmp_monitoring_snmpinterfacestats',
                    'timestamp',
                    migrate_data => true,
                    if_not_exists => TRUE,
                    create_default_indexes => FALSE,
                    chunk_time_interval => INTERVAL '1 day'
                );
            """,
            reverse_sql="""
                -- Safely drop hypertable only if it exists and is actually a hypertable
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM timescaledb_information.hypertables
                        WHERE hypertable_name = 'snmp_monitoring_snmpinterfacestats'
                    ) THEN
                        PERFORM drop_hypertable('snmp_monitoring_snmpinterfacestats', IF_EXISTS => TRUE);
                    END IF;
                END $$;
            """
        ),
    ]


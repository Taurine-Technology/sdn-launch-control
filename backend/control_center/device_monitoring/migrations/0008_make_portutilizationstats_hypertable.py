# Migration to convert PortUtilizationStats to TimescaleDB hypertable

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False  # The hypertable conversion must run outside of a transaction.

    dependencies = [
        ('device_monitoring', '0007_alter_portutilizationstats_primary_key'),
    ]

    operations = [
        # Ensure TimescaleDB extension exists before attempting hypertable operations
        migrations.RunSQL(
            sql="""
                CREATE EXTENSION IF NOT EXISTS timescaledb;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
        # Convert table to TimescaleDB hypertable
        migrations.RunSQL(
            sql="""
                SELECT create_hypertable(
                    'device_monitoring_portutilizationstats',
                    'timestamp',
                    migrate_data => true,
                    if_not_exists => TRUE
                );
            """,
            reverse_sql="""
                -- Safely drop hypertable only if it exists and is actually a hypertable
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM timescaledb_information.hypertables
                        WHERE hypertable_name = 'device_monitoring_portutilizationstats'
                    ) THEN
                        PERFORM drop_hypertable('device_monitoring_portutilizationstats', IF_EXISTS => TRUE);
                    END IF;
                END $$;
            """
        ),
    ]

# Migration to convert PortUtilizationStats to TimescaleDB hypertable

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False  # The hypertable conversion must run outside of a transaction.

    dependencies = [
        ('device_monitoring', '0007_alter_portutilizationstats_primary_key'),
    ]

    operations = [
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
                SELECT drop_hypertable('device_monitoring_portutilizationstats'::regclass);
            """
        ),
    ]

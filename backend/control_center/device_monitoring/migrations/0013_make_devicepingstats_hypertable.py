from django.db import migrations


def create_hypertable(apps, schema_editor):
    """
    Convert DevicePingStats table to a TimescaleDB hypertable.
    """
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT create_hypertable(
                'device_monitoring_devicepingstats',
                'timestamp',
                chunk_time_interval => INTERVAL '7 days',
                if_not_exists => TRUE
            );
        """)
        print("Created TimescaleDB hypertable for DevicePingStats")


def reverse_hypertable(apps, schema_editor):
    """
    Reverse migration is not supported for hypertables.
    """
    pass


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('device_monitoring', '0012_alter_devicepingstats_primary_key'),
    ]

    operations = [
        migrations.RunPython(create_hypertable, reverse_hypertable),
    ]
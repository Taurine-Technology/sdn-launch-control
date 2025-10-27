# Migration to alter DeviceStats primary key to include timestamp

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False  # Altering primary keys typically cannot run inside a transaction

    dependencies = [
        ('device_monitoring', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Drop the automatically created primary key constraint.
                ALTER TABLE device_monitoring_devicestats DROP CONSTRAINT device_monitoring_devicestats_pkey;
                -- Create a composite primary key including the partitioning column (timestamp) and the id.
                ALTER TABLE device_monitoring_devicestats ADD PRIMARY KEY (timestamp, id);
            """,
            reverse_sql="""
                -- Reverse: Drop the composite primary key and restore the original primary key on id.
                ALTER TABLE device_monitoring_devicestats DROP CONSTRAINT device_monitoring_devicestats_pkey;
                ALTER TABLE device_monitoring_devicestats ADD PRIMARY KEY (id);
            """,
        ),
    ]


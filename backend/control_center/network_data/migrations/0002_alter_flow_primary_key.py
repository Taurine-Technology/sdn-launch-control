# 0002_alter_flow_primary_key.py

from django.db import migrations

class Migration(migrations.Migration):
    atomic = False  # Altering primary keys typically cannot run inside a transaction

    dependencies = [
        ('network_data', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Drop the automatically created primary key constraint.
                ALTER TABLE network_data_flow DROP CONSTRAINT network_data_flow_pkey;
                -- Create a composite primary key including the partitioning column (timestamp) and the id.
                ALTER TABLE network_data_flow ADD PRIMARY KEY (timestamp, id);
            """,
            reverse_sql="""
                -- Reverse: Drop the composite primary key and restore the original primary key on id.
                ALTER TABLE network_data_flow DROP CONSTRAINT network_data_flow_pkey;
                ALTER TABLE network_data_flow ADD PRIMARY KEY (id);
            """,
        ),
    ]

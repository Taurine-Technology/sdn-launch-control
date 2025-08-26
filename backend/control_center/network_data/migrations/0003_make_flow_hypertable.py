# 0003_make_flow_hypertable.py

from django.db import migrations

class Migration(migrations.Migration):
    atomic = False  # The hypertable conversion must run outside of a transaction.

    dependencies = [
        ('network_data', '0002_alter_flow_primary_key'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                SELECT create_hypertable(
                    'network_data_flow',
                    'timestamp',
                    if_not_exists => TRUE
                );
            """,
            reverse_sql="""
                SELECT drop_hypertable('network_data_flow'::regclass);
            """,
        ),
    ]

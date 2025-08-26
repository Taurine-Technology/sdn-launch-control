from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('network_data', '0008_alter_flowstat_primary_key'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                SELECT create_hypertable(
                    'network_data_flowstat',
                    'timestamp',
                    migrate_data => true,
                    if_not_exists => TRUE
                );
            """,
            reverse_sql="""
                SELECT drop_hypertable('network_data_flowstat'::regclass);
            """
        ),
    ]

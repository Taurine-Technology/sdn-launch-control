# Generated migration for device_monitoring app

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(db_index=True)),
                ('cpu', models.FloatField(help_text='CPU usage percentage')),
                ('memory', models.FloatField(help_text='Memory usage percentage')),
                ('disk', models.FloatField(help_text='Disk usage percentage')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='DeviceHealthAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(unique=True)),
                ('last_cpu_alert', models.DateTimeField(blank=True, null=True)),
                ('last_memory_alert', models.DateTimeField(blank=True, null=True)),
                ('last_disk_alert', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.AddIndex(
            model_name='devicestats',
            index=models.Index(fields=['ip_address', 'timestamp'], name='device_moni_ip_addr_idx'),
        ),
        migrations.AddIndex(
            model_name='devicestats',
            index=models.Index(fields=['timestamp'], name='device_moni_timesta_idx'),
        ),
    ]


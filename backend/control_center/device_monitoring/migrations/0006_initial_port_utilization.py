# Generated migration for PortUtilizationStats and PortUtilizationAlert models

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('device_monitoring', '0005_rename_device_moni_ip_addr_idx_device_moni_ip_addr_9b306b_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PortUtilizationStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(db_index=True, help_text='IP address of the device')),
                ('port_name', models.CharField(db_index=True, help_text='Name of the port/interface', max_length=100)),
                ('throughput_mbps', models.FloatField(help_text='Calculated throughput in Mbps')),
                ('utilization_percent', models.FloatField(blank=True, help_text='Percentage of link capacity used (NULL if link_speed unknown)', null=True)),
                ('rx_bytes_diff', models.BigIntegerField(help_text='Received bytes delta from previous measurement')),
                ('tx_bytes_diff', models.BigIntegerField(help_text='Transmitted bytes delta from previous measurement')),
                ('duration_diff', models.FloatField(help_text='Time period for the measurement in seconds')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='PortUtilizationAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(db_index=True)),
                ('port_name', models.CharField(db_index=True, max_length=100)),
                ('last_utilization_alert', models.DateTimeField(blank=True, null=True)),
                ('last_null_link_speed_alert', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.AddIndex(
            model_name='portutilizationstats',
            index=models.Index(fields=['ip_address', 'port_name', 'timestamp'], name='port_util_stats_ip_port_time_idx'),
        ),
        migrations.AddIndex(
            model_name='portutilizationstats',
            index=models.Index(fields=['ip_address', 'timestamp'], name='port_util_stats_ip_time_idx'),
        ),
        migrations.AddIndex(
            model_name='portutilizationstats',
            index=models.Index(fields=['timestamp'], name='port_util_stats_time_idx'),
        ),
        migrations.AddConstraint(
            model_name='portutilizationalert',
            constraint=models.UniqueConstraint(fields=('ip_address', 'port_name'), name='unique_port_alert_per_device'),
        ),
    ]

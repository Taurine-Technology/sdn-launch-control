# Generated by Django 5.0.1 on 2024-02-05 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0005_alter_port_bridge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='os_type',
            field=models.CharField(choices=[('ubuntu_20_server', 'Ubuntu 20 Server'), ('ubuntu_22_server', 'Ubuntu 22 Server'), ('other', 'Other')], max_length=20),
        ),
    ]

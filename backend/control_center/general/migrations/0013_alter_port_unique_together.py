# Generated by Django 5.0.1 on 2024-03-25 10:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0012_remove_controller_lan_ip_address'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='port',
            unique_together={('device', 'name')},
        ),
    ]

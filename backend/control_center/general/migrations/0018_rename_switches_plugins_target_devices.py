# Generated by Django 5.0.1 on 2024-06-11 10:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0017_plugins_switches'),
    ]

    operations = [
        migrations.RenameField(
            model_name='plugins',
            old_name='switches',
            new_name='target_devices',
        ),
    ]

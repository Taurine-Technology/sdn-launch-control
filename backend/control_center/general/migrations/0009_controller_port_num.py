# Generated by Django 5.0.1 on 2024-02-08 11:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0008_alter_controller_device_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='controller',
            name='port_num',
            field=models.IntegerField(default=6653),
        ),
    ]
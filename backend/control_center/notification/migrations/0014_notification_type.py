# Generated migration for adding type field to Notification

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0013_alter_notification_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='type',
            field=models.CharField(
                choices=[
                    ('DEVICE_RESOURCE', 'Device Resource'),
                    ('NETWORK_SUMMARY', 'Network Summary'),
                    ('DATA_USAGE', 'Data Usage'),
                    ('APPLICATION_USAGE', 'Application Usage'),
                    ('OTHER', 'Other')
                ],
                default='OTHER',
                db_index=True,
                max_length=20
            ),
        ),
    ]


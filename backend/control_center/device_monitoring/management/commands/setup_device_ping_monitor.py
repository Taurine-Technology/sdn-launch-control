"""
Management command to set up device ping monitoring periodic task
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, PeriodicTasks, IntervalSchedule
import json


class Command(BaseCommand):
    help = 'Sets up the device ping monitoring periodic task'

    def handle(self, *_args, **_options):
        # Create or get the interval schedule (every 60 seconds)
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=60,
            period=IntervalSchedule.SECONDS,
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Created 60-second interval schedule'))

        # Create or update the periodic task (idempotent - won't recreate if exists)
        task_name = 'ping_all_monitored_devices'
        task, task_created = PeriodicTask.objects.get_or_create(
            name=task_name,
            defaults={
                'interval': schedule,
                'task': 'device_monitoring.tasks.ping_all_monitored_devices',
                'args': json.dumps([]),
                'enabled': True,
            }
        )

        if not task_created:
            # Update existing task if needed
            task.interval = schedule
            task.task = 'device_monitoring.tasks.ping_all_monitored_devices'
            task.args = json.dumps([])
            task.enabled = True
            task.save()
            self.stdout.write(self.style.SUCCESS(f'Updated periodic task: {task_name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Created periodic task: {task_name}'))

        # Notify celery-beat to reload the schedule immediately
        PeriodicTasks.changed(task)

        self.stdout.write(self.style.SUCCESS('Device ping monitoring is now scheduled to run every 60 seconds'))

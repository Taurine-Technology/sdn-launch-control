"""
Management command to set up device health monitoring periodic task
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json


class Command(BaseCommand):
    help = 'Sets up the device health monitoring periodic task'

    def handle(self, *args, **options):
        # Create or get the interval schedule (every 5 seconds)
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.SECONDS,
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Created 5-second interval schedule'))

        # Create or update the periodic task
        task_name = 'device_health_check'
        task, task_created = PeriodicTask.objects.get_or_create(
            name=task_name,
            defaults={
                'interval': schedule,
                'task': 'device_monitoring.tasks.check_device_health',
                'args': json.dumps([]),
            }
        )

        if not task_created:
            # Update existing task
            task.interval = schedule
            task.task = 'device_monitoring.tasks.check_device_health'
            task.args = json.dumps([])
            task.enabled = True
            task.save()
            self.stdout.write(self.style.SUCCESS(f'Updated periodic task: {task_name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Created periodic task: {task_name}'))

        self.stdout.write(self.style.SUCCESS('Device health monitoring is now scheduled to run every 5 seconds'))


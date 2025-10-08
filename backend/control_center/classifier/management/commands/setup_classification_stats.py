"""
Django Management Command: setup_classification_stats

This command sets up the periodic task in the DATABASE to save classification statistics.

NOTE: The task is already registered in celery.py and runs automatically.
This command is OPTIONAL and only needed if you want to manage the task via Django admin
instead of the code-based schedule.
"""

from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json


class Command(BaseCommand):
    help = '(OPTIONAL) Setup database-based periodic task for classification stats. Task already runs from celery.py.'

    def handle(self, *args, **options):
        # Create or get 5-minute interval schedule
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.MINUTES,
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created 5-minute interval schedule'))
        else:
            self.stdout.write(self.style.NOTICE('⏭️  5-minute interval schedule already exists'))
        
        # Create or update periodic task
        task, task_created = PeriodicTask.objects.get_or_create(
            name='Save Classification Statistics',
            defaults={
                'task': 'classifier.tasks.save_classification_statistics',
                'interval': schedule,
                'enabled': True,
            }
        )
        
        if task_created:
            self.stdout.write(self.style.SUCCESS(
                '✅ Created periodic task: "Save Classification Statistics"'
            ))
            self.stdout.write(f'   Task: {task.task}')
            self.stdout.write(f'   Interval: Every {schedule.every} {schedule.period}')
            self.stdout.write(f'   Status: {"Enabled" if task.enabled else "Disabled"}')
        else:
            # Update existing task if needed
            task.task = 'classifier.tasks.save_classification_statistics'
            task.interval = schedule
            task.enabled = True
            task.save()
            
            self.stdout.write(self.style.NOTICE(
                '🔄 Updated existing periodic task: "Save Classification Statistics"'
            ))
            self.stdout.write(f'   Task: {task.task}')
            self.stdout.write(f'   Interval: Every {schedule.every} {schedule.period}')
            self.stdout.write(f'   Status: {"Enabled" if task.enabled else "Disabled"}')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Setup Complete!'))
        self.stdout.write('Classification statistics will be saved every 5 minutes.')
        self.stdout.write('\nTo view statistics, run: python manage.py view_classification_stats')


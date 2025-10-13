"""
Django Management Command: setup_classification_stats

This command sets up the periodic task in the DATABASE to save classification statistics.

NOTE: The task is already registered in celery.py and runs automatically.
This command is OPTIONAL and only needed if you want to manage the task via Django admin
instead of the code-based schedule.
"""

from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule, PeriodicTasks


class Command(BaseCommand):
    help = '(OPTIONAL) Setup database-based periodic task for classification stats. Task already runs from celery.py.'

    def add_arguments(self, parser):
        """Add command arguments"""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if a code-based schedule might exist',
        )

    def handle(self, **options):
        """
        Setup database-based periodic task for classification statistics.
        
        WARNING: Ensure no code-based schedule exists in celery.py to avoid duplicate execution.
        """
        force = options.get('force', False)
        
        # Check if task already exists (potential duplicate schedule detection)
        existing_task = PeriodicTask.objects.filter(
            name='Save Classification Statistics'
        ).first()
        
        if existing_task and not force:
            self.stdout.write(self.style.WARNING(
                '⚠️  WARNING: Task "Save Classification Statistics" already exists in database!'
            ))
            self.stdout.write(self.style.WARNING(
                '   If a code-based schedule also exists in celery.py, this will cause duplicate execution.'
            ))
            self.stdout.write(f'   Current task status: {"Enabled" if existing_task.enabled else "Disabled"}')
            self.stdout.write('\n   To proceed anyway, run: python manage.py setup_classification_stats --force')
            return
        
        # Create or get 5-minute interval schedule
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.MINUTES,
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created 5-minute interval schedule'))
        else:
            self.stdout.write(self.style.WARNING('⏭️  5-minute interval schedule already exists'))
        
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
            
            self.stdout.write(self.style.WARNING(
                '🔄 Updated existing periodic task: "Save Classification Statistics"'
            ))
            self.stdout.write(f'   Task: {task.task}')
            self.stdout.write(f'   Interval: Every {schedule.every} {schedule.period}')
            self.stdout.write(f'   Status: {"Enabled" if task.enabled else "Disabled"}')
        
        # Notify django-celery-beat to reload schedules immediately
        PeriodicTasks.changed(task)
        self.stdout.write(self.style.SUCCESS('✅ Notified celery beat to reload schedules'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Setup Complete!'))
        self.stdout.write('Classification statistics will be saved every 5 minutes.')
        self.stdout.write('\n💡 NOTE: Ensure no code-based schedule exists in celery.py to avoid duplicate execution.')
        self.stdout.write('\nTo view statistics, run: python manage.py view_classification_stats')


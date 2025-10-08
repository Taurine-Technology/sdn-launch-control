"""
Celery configuration for SDN Launch Control
"""
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'control_center.settings')

app = Celery('control_center')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery configuration for better performance and reliability
app.conf.update(

    
    # Task execution settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=True,
    
    # Result backend settings
    result_backend=None,  # Disable result backend for better performance
    
    # Task execution timeouts
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    
    # Beat scheduler settings
    beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler',
    
    # Task compression
    task_compression='gzip',
    result_compression='gzip',
    
    # Task retry settings
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Worker pool settings
    worker_pool_restarts=True,
    
    # Database connection settings for Celery
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
)

# Note: Periodic tasks are managed via DatabaseScheduler (django_celery_beat)
# See docker-compose.yml for auto-setup via setup_classification_stats command
# To view/manage periodic tasks, use Django admin or management commands

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
"""
Database configuration for TimescaleDB with connection pooling
"""
import os
from django.conf import settings

# TimescaleDB specific database configuration
TIMESCALEDB_CONFIG = {
    'ENGINE': 'dj_db_conn_pool.backends.postgresql',
    'HOST': os.environ.get('DB_HOST'),
    'NAME': os.environ.get('DB_NAME'),
    'USER': os.environ.get('DB_USER'),
    'PASSWORD': os.environ.get('DB_PASS'),
    'PORT': os.environ.get('DB_PORT', '5432'),
    'POOL_OPTIONS': {
        'POOL_SIZE': int(os.environ.get('DB_MAX_CONNS', 20)),  # Maximum connections in pool
        'MAX_OVERFLOW': int(os.environ.get('DB_MAX_OVERFLOW', 10)),  # Additional connections when pool is full
        'RECYCLE': int(os.environ.get('DB_POOL_RECYCLE', 3600)),  # Recycle connections after 1 hour
    },
    'OPTIONS': {
        # TimescaleDB specific optimizations
        'application_name': 'sdn_launch_control',  # Helps with monitoring
        'connect_timeout': 10,  # Connection timeout in seconds
        'options': '-c timezone=UTC -c statement_timeout=300000',  # 5 minute statement timeout
    },
    'CONN_MAX_AGE': 0,  # Disable Django's built-in connection persistence since we're using pooling
    'ATOMIC_REQUESTS': False,  # Disable automatic transactions for better performance
}


# Development database configuration (with smaller pool for development)
DEV_DATABASE_CONFIG = {
    'ENGINE': 'dj_db_conn_pool.backends.postgresql',
    'HOST': os.environ.get('DB_HOST'),
    'NAME': os.environ.get('DB_NAME'),
    'USER': os.environ.get('DB_USER'),
    'PASSWORD': os.environ.get('DB_PASS'),
    'PORT': os.environ.get('DB_PORT', '5432'),
    'POOL_OPTIONS': {
        'POOL_SIZE': int(os.environ.get('DB_MAX_CONNS_DEV', 10)),  # Smaller pool for development
        'MAX_OVERFLOW': int(os.environ.get('DB_MAX_OVERFLOW_DEV', 5)),  # Smaller overflow for development
        'RECYCLE': int(os.environ.get('DB_POOL_RECYCLE', 3600)),  # Recycle connections after 1 hour
    },
    'OPTIONS': {
        'application_name': 'sdn_launch_control_dev',
        'connect_timeout': 10,
        'options': '-c timezone=UTC -c statement_timeout=300000',
    },
    'CONN_MAX_AGE': 0,
}


def get_database_config():
    """
    Get database configuration based on environment
    """
    # Check if we're running in a Celery worker
    is_celery_worker = os.environ.get('CELERY_WORKER_RUNNING', '0') == '1'
    
    if is_celery_worker:
        # For Celery workers, use standard PostgreSQL backend without connection pooling
        return {
            'ENGINE': 'django.db.backends.postgresql',
            'HOST': os.environ.get('DB_HOST'),
            'NAME': os.environ.get('DB_NAME'),
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('DB_PASS'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'OPTIONS': {
                'application_name': 'sdn_launch_control_celery',
                'connect_timeout': 10,
            },
            'CONN_MAX_AGE': 30,
        }
    
    # For Django web server
    if settings.DEBUG:
        return DEV_DATABASE_CONFIG
    return TIMESCALEDB_CONFIG

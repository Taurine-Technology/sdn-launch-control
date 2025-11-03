"""
Connection pool setup for django-db-connection-pool
"""
import os
import dj_db_conn_pool
from django.conf import settings
from dj_db_conn_pool.core import pool_container

def setup_connection_pool():
    """
    Setup connection pool with default parameters
    This should be called before any database operations
    """
    # Don't setup connection pooling for Celery workers
    is_celery_worker = os.environ.get('CELERY_WORKER_RUNNING', '0') == '1'
    if is_celery_worker:
        print("Skipping connection pool setup for Celery worker")
        return
    
    # Get pool configuration from environment or use defaults
    pool_size = int(os.environ.get('DB_MAX_CONNS', 20))
    max_overflow = int(os.environ.get('DB_MAX_OVERFLOW', 10))
    recycle = int(os.environ.get('DB_POOL_RECYCLE', 3600))
    
    # Setup the connection pool with default parameters
    dj_db_conn_pool.setup(
        pool_size=pool_size,
        max_overflow=max_overflow,
        recycle=recycle
    )
    
    print(f"Connection pool configured with:")
    print(f"  Pool Size: {pool_size}")
    print(f"  Max Overflow: {max_overflow}")
    print(f"  Recycle: {recycle}s")


def setup_dev_connection_pool():
    """
    Setup connection pool for development environment
    """
    # Don't setup connection pooling for Celery workers
    is_celery_worker = os.environ.get('CELERY_WORKER_RUNNING', '0') == '1'
    if is_celery_worker:
        print("Skipping connection pool setup for Celery worker")
        return
    
    # Get development pool configuration
    pool_size = int(os.environ.get('DB_MAX_CONNS_DEV', 10))
    max_overflow = int(os.environ.get('DB_MAX_OVERFLOW_DEV', 5))
    recycle = int(os.environ.get('DB_POOL_RECYCLE', 3600))
    
    # Setup the connection pool with development parameters
    dj_db_conn_pool.setup(
        pool_size=pool_size,
        max_overflow=max_overflow,
        recycle=recycle
    )
    
    print(f"Development connection pool configured with:")
    print(f"  Pool Size: {pool_size}")
    print(f"  Max Overflow: {max_overflow}")
    print(f"  Recycle: {recycle}s")


def get_pool_stats():
    """
    Get current pool statistics
    """
    try:
        
        
        stats = {
            'total_pools': len(pool_container.pools),
            'pools': {}
        }
        
        for alias, pool in pool_container.pools.items():
            stats['pools'][alias] = {
                'size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid()
            }
        
        return stats
    except Exception as e:
        print(f"Error getting pool stats: {e}")
        return None

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
    Get current pool statistics across all configured aliases.

    This uses best-effort introspection to support multiple versions of
    django-db-connection-pool where the container API changed.

    References:
      - PyPI: https://pypi.org/project/django-db-connection-pool/
      - Source (PoolContainer): https://github.com/altairbow/django-db-connection-pool
    """
    try:
        # Candidate locations for the internal pools mapping in different releases
        candidate_attrs = (
            'pools',            # older versions
            '_pools',           # private attribute in some versions
            'pool_map',         # alternative naming
            'db_pools',         # alternative naming
        )

        pools_mapping = None
        for attr in candidate_attrs:
            if hasattr(pool_container, attr):
                value = getattr(pool_container, attr)
                if isinstance(value, dict) and value:
                    pools_mapping = value
                    break

        # As a fallback, introspect any dict attribute holding pool-like objects
        if pools_mapping is None:
            for name in dir(pool_container):
                try:
                    value = getattr(pool_container, name)
                except Exception:
                    continue
                if isinstance(value, dict) and value:
                    # Heuristic: values implement SQLAlchemy pool API
                    any_val = next(iter(value.values()))
                    if all(hasattr(any_val, m) for m in ('size', 'checkedin', 'checkedout', 'overflow')):
                        pools_mapping = value
                        break

        if pools_mapping is None:
            # Nothing found; return empty so callers can skip emitting warnings
            return {
                'total_pools': 0,
                'pools': {}
            }

        stats = {
            'total_pools': len(pools_mapping),
            'pools': {}
        }

        for alias, pool in pools_mapping.items():
            try:
                stats['pools'][alias] = {
                    'size': pool.size(),
                    'checked_in': pool.checkedin(),
                    'checked_out': pool.checkedout(),
                    'overflow': pool.overflow(),
                    'invalid': getattr(pool, 'invalid', lambda: 0)(),
                }
            except Exception:
                # Skip aliases we cannot introspect
                continue

        return stats
    except Exception as e:
        print(f"Error getting pool stats: {e}")
        return None

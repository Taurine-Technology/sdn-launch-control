"""
Database utility functions for connection management and monitoring
"""
import logging
import time
from contextlib import contextmanager
from django.db import connection, transaction
from django.conf import settings

logger = logging.getLogger(__name__)


@contextmanager
def db_connection_monitor(operation_name="database_operation"):
    """
    Context manager to monitor database connections and log performance
    """
    start_time = time.time()
    connection_id = None
    
    try:
        # Get connection info before operation
        if hasattr(connection, 'connection') and connection.connection:
            connection_id = id(connection.connection)
        
        yield
        
    except Exception as e:
        logger.error(f"Database error in {operation_name}: {e}")
        raise
    finally:
        # Log operation completion
        duration = time.time() - start_time
        if duration > 1.0:  # Log slow operations
            logger.warning(
                f"Slow database operation '{operation_name}' took {duration:.2f}s "
                f"(connection_id: {connection_id})"
            )
        elif settings.DEBUG:
            logger.debug(
                f"Database operation '{operation_name}' took {duration:.3f}s "
                f"(connection_id: {connection_id})"
            )


def get_connection_info():
    """
    Get current database connection information
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT current_database(), current_user, inet_server_addr()")
            db_info = cursor.fetchone()
            
            return {
                'version': version,
                'database': db_info[0],
                'user': db_info[1],
                'host': db_info[2],
                'connection_id': id(connection.connection) if hasattr(connection, 'connection') else None,
            }
    except Exception as e:
        logger.error(f"Error getting connection info: {e}")
        return None


def check_connection_health():
    """
    Check if the database connection is healthy
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            return result[0] == 1
    except Exception as e:
        logger.error(f"Database connection health check failed: {e}")
        return False


def get_active_connections():
    """
    Get information about active database connections
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    pid,
                    usename,
                    application_name,
                    client_addr,
                    state,
                    query_start,
                    query
                FROM pg_stat_activity 
                WHERE datname = current_database()
                AND state != 'idle'
                ORDER BY query_start DESC
            """)
            
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting active connections: {e}")
        return []


def optimize_timescaledb_queries():
    """
    Apply TimescaleDB specific optimizations
    """
    try:
        with connection.cursor() as cursor:
            # Set TimescaleDB specific parameters
            cursor.execute("SET timescaledb.max_background_workers = 8")
            cursor.execute("SET timescaledb.license = 'apache'")
            
            # Set query optimization parameters
            cursor.execute("SET random_page_cost = 1.1")  # Optimized for SSD
            cursor.execute("SET effective_cache_size = '4GB'")  # Adjust based on your system
            cursor.execute("SET work_mem = '256MB'")  # Adjust based on your workload
            
            logger.info("TimescaleDB optimizations applied")
            
    except Exception as e:
        logger.error(f"Error applying TimescaleDB optimizations: {e}")


@contextmanager
def managed_transaction():
    """
    Context manager for managed database transactions with connection pooling
    """
    try:
        with transaction.atomic():
            yield
    except Exception as e:
        logger.error(f"Transaction error: {e}")
        raise
    finally:
        # Ensure connection is properly managed
        if hasattr(connection, 'close') and not connection.in_atomic_block:
            connection.close()


def log_connection_pool_stats():
    """
    Log connection pool statistics
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections,
                    count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            
            stats = cursor.fetchone()
            
            logger.info(
                f"Connection pool stats - Total: {stats[0]}, "
                f"Active: {stats[1]}, Idle: {stats[2]}, "
                f"Idle in transaction: {stats[3]}"
            )
            
            return {
                'total': stats[0],
                'active': stats[1],
                'idle': stats[2],
                'idle_in_transaction': stats[3]
            }
            
    except Exception as e:
        logger.error(f"Error getting connection pool stats: {e}")
        return None

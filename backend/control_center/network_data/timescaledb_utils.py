"""
TimescaleDB utility functions for network_data app
"""
from django.db import connection
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def get_hypertable_info():
    """
    Get information about TimescaleDB hypertables
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    hypertable_name,
                    num_chunks,
                    compression_enabled
                FROM timescaledb_information.hypertables
                WHERE hypertable_schema = 'public'
                ORDER BY hypertable_name;
            """)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting hypertable info: {e}")
        return []


def get_chunk_info(table_name):
    """
    Get chunk information for a specific hypertable
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    chunk_name,
                    range_start,
                    range_end,
                    is_compressed,
                    chunk_size,
                    index_size
                FROM timescaledb_information.chunks
                WHERE hypertable_name = %s
                ORDER BY range_start DESC
                LIMIT 10;
            """, [table_name])
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting chunk info for {table_name}: {e}")
        return []


def get_continuous_aggregate_info():
    """
    Get information about continuous aggregates
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    view_name,
                    materialized_only,
                    compression_enabled
                FROM timescaledb_information.continuous_aggregates
                WHERE view_schema = 'public'
                ORDER BY view_name;
            """)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting continuous aggregate info: {e}")
        return []


def get_compression_stats():
    """
    Get compression statistics
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    hypertable_name,
                    COUNT(*) as compression_columns,
                    STRING_AGG(attname, ', ') as segmentby_columns
                FROM timescaledb_information.compression_settings
                WHERE hypertable_schema = 'public'
                GROUP BY hypertable_name
                ORDER BY hypertable_name;
            """)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting compression stats: {e}")
        return []


def refresh_continuous_aggregate(view_name, start_time=None, end_time=None):
    """
    Manually refresh a continuous aggregate
    """
    try:
        with connection.cursor() as cursor:
            if start_time and end_time:
                cursor.execute("""
                    CALL refresh_continuous_aggregate(%s, %s, %s);
                """, [view_name, start_time, end_time])
            else:
                cursor.execute("""
                    CALL refresh_continuous_aggregate(%s, NULL, NULL);
                """, [view_name])
            return True
    except Exception as e:
        logger.error(f"Error refreshing continuous aggregate {view_name}: {e}")
        return False


def compress_chunks(table_name, older_than=None):
    """
    Manually compress chunks for a hypertable
    """
    try:
        with connection.cursor() as cursor:
            if older_than:
                cursor.execute("""
                    SELECT compress_chunk(chunk_name)
                    FROM timescaledb_information.chunks
                    WHERE hypertable_name = %s
                    AND range_start < NOW() - %s::interval
                    AND NOT is_compressed;
                """, [table_name, older_than])
            else:
                cursor.execute("""
                    SELECT compress_chunk(chunk_name)
                    FROM timescaledb_information.chunks
                    WHERE hypertable_name = %s
                    AND NOT is_compressed;
                """, [table_name])
            return True
    except Exception as e:
        logger.error(f"Error compressing chunks for {table_name}: {e}")
        return False


def get_timescaledb_version():
    """
    Get TimescaleDB version information
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT default_version, installed_version FROM pg_available_extensions WHERE name = 'timescaledb';")
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error getting TimescaleDB version: {e}")
        return None


def optimize_timescaledb_settings():
    """
    Apply TimescaleDB-specific optimizations
    """
    try:
        with connection.cursor() as cursor:
            # Set TimescaleDB specific parameters for better performance
            cursor.execute("SET timescaledb.max_background_workers = 8")
            cursor.execute("SET timescaledb.license = 'apache'")
            
            # Set query optimization parameters
            cursor.execute("SET random_page_cost = 1.1")  # Optimized for SSD
            cursor.execute("SET effective_cache_size = '4GB'")  # Adjust based on your system
            cursor.execute("SET work_mem = '256MB'")  # Adjust based on your workload
            
            # Set maintenance parameters
            cursor.execute("SET maintenance_work_mem = '512MB'")
            cursor.execute("SET autovacuum_vacuum_scale_factor = 0.1")
            cursor.execute("SET autovacuum_analyze_scale_factor = 0.05")
            
            logger.info("TimescaleDB optimizations applied successfully")
            return True
    except Exception as e:
        logger.error(f"Error applying TimescaleDB optimizations: {e}")
        return False


def get_query_performance_stats():
    """
    Get query performance statistics for TimescaleDB
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements
                WHERE query LIKE '%timescaledb%'
                   OR query LIKE '%time_bucket%'
                   OR query LIKE '%network_data_flow%'
                   OR query LIKE '%network_data_flowstat%'
                ORDER BY total_time DESC
                LIMIT 10;
            """)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting query performance stats: {e}")
        return []

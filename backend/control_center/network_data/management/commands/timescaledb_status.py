"""
Management command to check TimescaleDB status and performance
"""
from django.core.management.base import BaseCommand
from django.db import connection
from network_data.timescaledb_utils import (
    get_hypertable_info,
    get_chunk_info,
    get_continuous_aggregate_info,
    get_compression_stats,
    get_timescaledb_version,
    optimize_timescaledb_settings
)


class Command(BaseCommand):
    help = 'Check TimescaleDB status and performance metrics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed information including chunk details',
        )
        parser.add_argument(
            '--optimize',
            action='store_true',
            help='Apply TimescaleDB optimizations',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== TimescaleDB Status Report ===')
        )
        
        # Check TimescaleDB version
        version_info = get_timescaledb_version()
        if version_info:
            default_version, installed_version = version_info
            self.stdout.write(f"TimescaleDB Version: {installed_version}")
        
        # Get hypertable information
        self.stdout.write("\n--- Hypertables ---")
        hypertables = get_hypertable_info()
        for table_name, num_chunks, compression_enabled in hypertables:
            self.stdout.write(
                f"Table: {table_name}, "
                f"Chunks: {num_chunks}, "
                f"Compression: {'Enabled' if compression_enabled else 'Disabled'}"
            )
            
            if options['detailed']:
                chunks = get_chunk_info(table_name)
                if chunks:
                    self.stdout.write(f"  Recent chunks for {table_name}:")
                    for chunk_name, range_start, range_end, is_compressed, chunk_size, index_size in chunks:
                        self.stdout.write(
                            f"    {chunk_name}: {range_start} to {range_end}, "
                            f"Size: {chunk_size}, "
                            f"Compressed: {'Yes' if is_compressed else 'No'}"
                        )
        
        # Get continuous aggregate information
        self.stdout.write("\n--- Continuous Aggregates ---")
        continuous_aggregates = get_continuous_aggregate_info()
        for view_name, materialized_only, compression_enabled in continuous_aggregates:
            self.stdout.write(
                f"View: {view_name}, "
                f"Materialized Only: {'Yes' if materialized_only else 'No'}, "
                f"Compression: {'Enabled' if compression_enabled else 'Disabled'}"
            )
        
        # Get compression statistics
        self.stdout.write("\n--- Compression Statistics ---")
        compression_stats = get_compression_stats()
        if compression_stats:
            for table_name, compression_columns, segmentby_columns in compression_stats:
                self.stdout.write(
                    f"Table: {table_name}, "
                    f"Compression Columns: {compression_columns}, "
                    f"Segment By: {segmentby_columns}"
                )
        else:
            self.stdout.write("No compression statistics available")
        
        # Check chunk distribution
        self.stdout.write("\n--- Chunk Distribution ---")
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        hypertable_name,
                        COUNT(*) as total_chunks,
                        COUNT(*) FILTER (WHERE is_compressed) as compressed_chunks,
                        COUNT(*) FILTER (WHERE NOT is_compressed) as uncompressed_chunks
                    FROM timescaledb_information.chunks
                    WHERE hypertable_schema = 'public'
                    GROUP BY hypertable_name
                    ORDER BY hypertable_name;
                """)
                chunk_distribution = cursor.fetchall()
                
                for table_name, total, compressed, uncompressed in chunk_distribution:
                    self.stdout.write(
                        f"Table: {table_name}, "
                        f"Total: {total}, "
                        f"Compressed: {compressed}, "
                        f"Uncompressed: {uncompressed}"
                    )
        except Exception as e:
            self.stdout.write(f"Error getting chunk distribution: {e}")
        
        # Check recent data insertion rates
        self.stdout.write("\n--- Recent Data Insertion Rates ---")
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        'network_data_flow' as table_name,
                        COUNT(*) as records_last_hour
                    FROM network_data_flow
                    WHERE timestamp >= NOW() - INTERVAL '1 hour'
                    UNION ALL
                    SELECT 
                        'network_data_flowstat' as table_name,
                        COUNT(*) as records_last_hour
                    FROM network_data_flowstat
                    WHERE timestamp >= NOW() - INTERVAL '1 hour';
                """)
                insertion_rates = cursor.fetchall()
                
                for table_name, records_last_hour in insertion_rates:
                    self.stdout.write(f"Table: {table_name}, Records (last hour): {records_last_hour}")
        except Exception as e:
            self.stdout.write(f"Error getting insertion rates: {e}")
        
        # Apply optimizations if requested
        if options['optimize']:
            self.stdout.write("\n--- Applying TimescaleDB Optimizations ---")
            if optimize_timescaledb_settings():
                self.stdout.write(
                    self.style.SUCCESS("TimescaleDB optimizations applied successfully")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("Failed to apply TimescaleDB optimizations")
                )
        
        self.stdout.write("\n=== TimescaleDB Status Report Complete ===")

"""
Management command to check database connection pool status
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import psycopg2
import os


class Command(BaseCommand):
    help = 'Check database connection pool status and active connections'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed connection information',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Database Connection Pool Status ===')
        )
        
        # Get database configuration
        db_config = settings.DATABASES['default']
        
        self.stdout.write(f"Database Engine: {db_config['ENGINE']}")
        self.stdout.write(f"Database Host: {db_config['HOST']}")
        self.stdout.write(f"Database Name: {db_config['NAME']}")
        
        if 'POOL_OPTIONS' in db_config:
            pool_options = db_config['POOL_OPTIONS']
            self.stdout.write(f"Pool Size: {pool_options.get('POOL_SIZE', 'Not set')}")
            self.stdout.write(f"Max Overflow: {pool_options.get('MAX_OVERFLOW', 'Not set')}")
            self.stdout.write(f"Recycle: {pool_options.get('RECYCLE', 'Not set')}s")
        
        # Check active connections to the database
        try:
            with connection.cursor() as cursor:
                # Get current active connections
                cursor.execute("""
                    SELECT 
                        pid,
                        usename,
                        application_name,
                        client_addr,
                        state,
                        query_start,
                        state_change,
                        query
                    FROM pg_stat_activity 
                    WHERE datname = %s 
                    AND state != 'idle'
                    ORDER BY query_start DESC
                """, [db_config['NAME']])
                
                active_connections = cursor.fetchall()
                
                self.stdout.write(f"\nActive Connections: {len(active_connections)}")
                
                if options['detailed'] and active_connections:
                    self.stdout.write("\nDetailed Connection Information:")
                    for conn in active_connections:
                        self.stdout.write(
                            f"PID: {conn[0]}, User: {conn[1]}, App: {conn[2]}, "
                            f"Client: {conn[3]}, State: {conn[4]}, "
                            f"Started: {conn[5]}, Query: {conn[7][:100]}..."
                        )
                
                # Get connection pool statistics if using connection pooling
                if 'dj_db_conn_pool' in db_config['ENGINE']:
                    cursor.execute("""
                        SELECT 
                            count(*) as total_connections,
                            count(*) FILTER (WHERE state = 'active') as active_connections,
                            count(*) FILTER (WHERE state = 'idle') as idle_connections
                        FROM pg_stat_activity 
                        WHERE datname = %s
                    """, [db_config['NAME']])
                    
                    pool_stats = cursor.fetchone()
                    if pool_stats:
                        self.stdout.write(f"\nConnection Pool Statistics:")
                        self.stdout.write(f"Total Connections: {pool_stats[0]}")
                        self.stdout.write(f"Active Connections: {pool_stats[1]}")
                        self.stdout.write(f"Idle Connections: {pool_stats[2]}")
                
                # Check for long-running queries
                cursor.execute("""
                    SELECT 
                        pid,
                        usename,
                        application_name,
                        query_start,
                        state,
                        query
                    FROM pg_stat_activity 
                    WHERE datname = %s 
                    AND state = 'active'
                    AND query_start < NOW() - INTERVAL '5 minutes'
                    ORDER BY query_start ASC
                """, [db_config['NAME']])
                
                long_running = cursor.fetchall()
                
                if long_running:
                    self.stdout.write(
                        self.style.WARNING(f"\nLong-running queries (>5 minutes): {len(long_running)}")
                    )
                    for query in long_running:
                        self.stdout.write(
                            f"PID: {query[0]}, User: {query[1]}, "
                            f"Started: {query[3]}, Query: {query[5][:100]}..."
                        )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error checking database status: {e}")
            )
        
        # Test connection pool
        self.stdout.write("\n=== Testing Connection Pool ===")
        try:
            # Test multiple connections
            connections = []
            for i in range(5):
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    connections.append(result[0])
            
            self.stdout.write(
                self.style.SUCCESS(f"Successfully tested {len(connections)} connections")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error testing connections: {e}")
            )

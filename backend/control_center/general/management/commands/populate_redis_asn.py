import csv
import ipaddress
import os
from django.core.management.base import BaseCommand
from django.conf import settings
import redis


class Command(BaseCommand):
    help = 'Populate Redis with IP-to-ASN mapping data from GeoLite2 CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            help='Path to the GeoLite2-ASN-Blocks-IPv4.csv file',
            default=None
        )
        parser.add_argument(
            '--redis-key',
            type=str,
            help='Redis key for the IP-to-ASN mapping',
            default='ip_asn_map'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            help='Batch size for Redis pipeline operations',
            default=1000
        )

    def handle(self, *args, **options):
        # Constants
        REDIS_KEY = options['redis_key']
        BATCH_SIZE = options['batch_size']

        # Determine CSV file path
        if options['csv_file']:
            CSV_FILE_PATH = options['csv_file']
        else:
            # Default to the data directory in the project
            CSV_FILE_PATH = os.path.join(
                settings.BASE_DIR,
                'data',
                'GeoLite2-ASN-Blocks-IPv4.csv'
            )

        # Validate CSV file exists
        if not os.path.exists(CSV_FILE_PATH):
            self.stdout.write(
                self.style.ERROR(f'CSV file not found: {CSV_FILE_PATH}')
            )
            return

        # Connect to Redis
        try:
            redis_host = getattr(settings, 'CHANNEL_REDIS_HOST', 'redis')
            redis_port = getattr(settings, 'CHANNEL_REDIS_PORT', 6379)

            redis_conn = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True
            )

            # Test connection
            redis_conn.ping()
            self.stdout.write(
                self.style.SUCCESS(f'Connected to Redis at {redis_host}:{redis_port}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to connect to Redis: {e}')
            )
            return

        # Clear existing data
        try:
            deleted_count = redis_conn.delete(REDIS_KEY)
            self.stdout.write(
                self.style.WARNING(f'Cleared existing data: {deleted_count} keys deleted')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to clear existing data: {e}')
            )
            return

        # Process CSV file
        try:
            total_records = 0
            processed_records = 0

            # First, count total records for progress reporting
            with open(CSV_FILE_PATH, 'r', encoding='utf-8') as csvfile:
                total_records = sum(1 for _ in csvfile) - 1  # Subtract header row

            self.stdout.write(
                self.style.SUCCESS(f'Found {total_records} records to process')
            )

            # Process records in batches
            with open(CSV_FILE_PATH, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Create pipeline for batch operations
                pipe = redis_conn.pipeline()
                batch_count = 0

                for row in reader:
                    try:
                        # Parse the CIDR network
                        network = ipaddress.ip_network(row['network'])

                        # Calculate start and end IP addresses
                        start_ip_int = int(network.network_address)
                        end_ip_int = int(network.broadcast_address)

                        # Format member string: "start_ip_int:asn:organization"
                        asn_num = row['autonomous_system_number']
                        org_name = row['autonomous_system_organization']
                        member = f"{start_ip_int}:{asn_num}:{org_name}"

                        # Add to pipeline
                        pipe.zadd(REDIS_KEY, {member: end_ip_int})
                        batch_count += 1
                        processed_records += 1

                        # Execute batch when batch size is reached
                        if batch_count >= BATCH_SIZE:
                            pipe.execute()
                            self.stdout.write(
                                f'Processed {processed_records}/{total_records} records '
                                f'({(processed_records/total_records)*100:.1f}%)'
                            )
                            pipe = redis_conn.pipeline()
                            batch_count = 0

                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Skipping invalid record: {row.get("network", "unknown")} - {e}'
                            )
                        )
                        continue

                # Execute remaining records in pipeline
                if batch_count > 0:
                    pipe.execute()

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully processed {processed_records} records'
                    )
                )

            # Verify data was inserted
            try:
                zset_size = redis_conn.zcard(REDIS_KEY)
                self.stdout.write(
                    self.style.SUCCESS(f'Redis ZSET size: {zset_size} records')
                )

                if zset_size > 0:
                    # Show a sample record
                    sample = redis_conn.zrange(REDIS_KEY, 0, 0, withscores=True)
                    if sample:
                        member, score = sample[0]
                        self.stdout.write(
                            self.style.SUCCESS(f'Sample record: {member} -> {score}')
                        )

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Could not verify data: {e}')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to process CSV file: {e}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS('IP-to-ASN lookup service population completed successfully!')
        )

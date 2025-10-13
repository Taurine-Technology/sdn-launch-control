"""
Django Management Command: load_dns_servers

This command loads DNS server IPs from the nameservers.csv file into Redis
for fast O(1) lookups during traffic classification.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from classifier.dns_loader import dns_loader, REDIS_DNS_KEY
import redis


class Command(BaseCommand):
    help = 'Load DNS server IPs from nameservers.csv into Redis for fast lookups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            help='Path to nameservers.csv file (defaults to data/nameservers.csv)',
            default=None
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            help='Number of IPs to add to Redis in each batch (default: 1000)',
            default=1000
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            help='Verify DNS server loading with sample IPs'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing DNS servers before loading'
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show current DNS server count in Redis'
        )

    def handle(self, *args, **options):
        csv_path = options.get('csv_path')
        batch_size = options.get('batch_size', 1000)
        verify = options.get('verify', False)
        clear_only = options.get('clear', False)
        show_status = options.get('status', False)
        
        # Connect to Redis (like ASN pattern)
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
            self.stdout.write(self.style.SUCCESS('✅ Redis connection healthy'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Redis is not accessible: {e}'))
            return
        
        # Show status if requested
        if show_status:
            current_count = redis_conn.scard(REDIS_DNS_KEY)
            self.stdout.write(f'Current DNS servers in Redis: {current_count:,}')
            return
        
        # Clear DNS servers if requested
        if clear_only:
            self.stdout.write(self.style.WARNING('Clearing DNS servers from Redis...'))
            try:
                redis_conn.delete(REDIS_DNS_KEY)
                self.stdout.write(self.style.SUCCESS('✅ DNS servers cleared from Redis'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed to clear DNS servers: {e}'))
            return
        
        # Initialize DNS loader with the tested Redis connection
        from classifier.dns_loader import DNSServerLoader
        loader = DNSServerLoader(csv_path, redis_conn=redis_conn) if csv_path else DNSServerLoader(redis_conn=redis_conn)
        
        self.stdout.write('Loading DNS servers from CSV into Redis...')
        self.stdout.write(f'   Batch size: {batch_size:,}')
        
        # Load DNS servers
        success, count, message = loader.load_dns_servers(batch_size=batch_size)
        
        if success:
            self.stdout.write(self.style.SUCCESS(f'✅ {message}'))
            self.stdout.write(self.style.SUCCESS(f'   Total DNS servers in Redis: {count:,}'))
            
            # Verify with sample IPs if requested
            if verify:
                self.stdout.write('\n Verifying DNS server detection...')
                sample_ips = loader.get_sample_dns_servers(count=10)
                
                verified_count = 0
                for ip in sample_ips:
                    if loader.verify_dns_server(ip):
                        self.stdout.write(self.style.SUCCESS(f'   ✅ {ip} - Verified'))
                        verified_count += 1
                    else:
                        self.stdout.write(self.style.ERROR(f'   ❌ {ip} - Not found'))
                
                self.stdout.write(self.style.SUCCESS(f'\n✅ Verified {verified_count}/{len(sample_ips)} sample IPs'))
                
                # Test some well-known DNS servers
                well_known_dns = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
                self.stdout.write('\n Testing well-known DNS servers...')
                
                for ip in well_known_dns:
                    if loader.redis_conn.sismember(REDIS_DNS_KEY, ip):
                        self.stdout.write(self.style.SUCCESS(f'   ✅ {ip} - Found'))
                    else:
                        self.stdout.write(self.style.WARNING(f'   ⚠️  {ip} - Not found (may not be in CSV)'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ {message}'))
            return
        
        # Final summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('DNS Server Loading Complete'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'Total DNS servers loaded: {count:,}')
        self.stdout.write('DNS detection is now ready for traffic classification! 🚀')


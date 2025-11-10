"""
Django Management Command: load_vpn_networks

This command loads VPN CIDR ranges from the vpn-ipv4.txt file into Redis
for fast lookups during traffic classification.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from classifier.vpn_loader import REDIS_VPN_KEY
import redis
from classifier.vpn_loader import VPNNetworkLoader
import ipaddress

class Command(BaseCommand):
    help = 'Load VPN CIDR ranges from vpn-ipv4.txt into Redis for fast lookups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--txt-path',
            type=str,
            help='Path to vpn-ipv4.txt file (defaults to data/vpn-ipv4.txt)',
            default=None
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            help='Number of CIDR ranges to add to Redis in each batch (default: 1000)',
            default=1000
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            help='Verify VPN network loading with sample IPs'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing VPN networks before loading'
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show current VPN network count in Redis'
        )

    def handle(self, *args, **options):
        txt_path = options.get('txt_path')
        batch_size = options.get('batch_size', 1000)
        verify = options.get('verify', False)
        clear_only = options.get('clear', False)
        show_status = options.get('status', False)
        
        # Connect to Redis (with same timeout/retry settings as VPNNetworkLoader)
        try:
            redis_host = getattr(settings, 'CHANNEL_REDIS_HOST', 'redis')
            redis_port = getattr(settings, 'CHANNEL_REDIS_PORT', 6379)
            redis_conn = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_timeout=5,           # 5 second timeout for operations
                socket_connect_timeout=5,   # 5 second timeout for connection
                retry_on_timeout=True       # Automatically retry once on timeout
            )
            # Test connection
            redis_conn.ping()
            self.stdout.write(self.style.SUCCESS('Redis connection healthy'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Redis is not accessible: {e}'))
            return
        
        # Show status if requested
        if show_status:
            current_count = redis_conn.scard(REDIS_VPN_KEY)
            self.stdout.write(f'Current VPN networks in Redis: {current_count:,}')
            return
        
        # Clear VPN networks if requested
        if clear_only:
            self.stdout.write(self.style.WARNING('Clearing VPN networks from Redis...'))
            try:
                redis_conn.delete(REDIS_VPN_KEY)
                self.stdout.write(self.style.SUCCESS('VPN networks cleared from Redis'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to clear VPN networks: {e}'))
            return
        
        # Initialize VPN loader with the tested Redis connection
        loader = VPNNetworkLoader(txt_path=txt_path, redis_conn=redis_conn)
        
        self.stdout.write('Loading VPN networks from text file into Redis...')
        self.stdout.write(f'   Batch size: {batch_size:,}')
        
        # Load VPN networks
        success, count, message = loader.load_vpn_networks(batch_size=batch_size)
        
        if success:
            self.stdout.write(self.style.SUCCESS(f'{message}'))
            self.stdout.write(self.style.SUCCESS(f'   Total VPN networks in Redis: {count:,}'))
            
            # Verify with sample IPs if requested
            if verify:
                self.stdout.write('\n Verifying VPN network detection...')
                sample_cidrs = loader.get_sample_vpn_networks(count=5)
                
                verified_count = 0
                for cidr in sample_cidrs:
                    # Extract a test IP from the CIDR range
                    try:
                        network = ipaddress.IPv4Network(cidr, strict=False)
                        # Use next() to get first host without materializing entire list (avoids OOM for large CIDRs)
                        # Falls back to network_address for /31 and /32 networks where hosts() is empty
                        test_ip = str(next(network.hosts(), network.network_address))
                        
                        if loader.verify_vpn_ip(test_ip):
                            self.stdout.write(self.style.SUCCESS(f'   {test_ip} (from {cidr}) - Verified'))
                            verified_count += 1
                        else:
                            self.stdout.write(self.style.ERROR(f'   {test_ip} (from {cidr}) - Not found'))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'   {cidr} - Error: {e}'))
                
                self.stdout.write(self.style.SUCCESS(f'\nVerified {verified_count}/{len(sample_cidrs)} sample IPs'))
        else:
            self.stdout.write(self.style.ERROR(f'{message}'))
            return
        
        # Final summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('VPN Network Loading Complete'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'Total VPN networks loaded: {count:,}')
        self.stdout.write('VPN detection is now ready for traffic classification!')


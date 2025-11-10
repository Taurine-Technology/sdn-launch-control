"""
Django Management Command: test_vpn_lookup

This command tests VPN IP lookup functionality with specific test cases.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from classifier.vpn_loader import VPNNetworkLoader, REDIS_VPN_KEY
import redis
import time

class Command(BaseCommand):
    help = 'Test VPN IP lookup functionality with specific test cases'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ip',
            type=str,
            help='Single IP address to test',
            default=None
        )
        parser.add_argument(
            '--load-first',
            action='store_true',
            help='Load VPN networks into Redis before testing (if not already loaded)',
            default=False
        )

    def handle(self, *args, **options):
        test_ip = options.get('ip')
        load_first = options.get('load_first', False)
        
        # Connect to Redis
        try:
            redis_host = getattr(settings, 'CHANNEL_REDIS_HOST', 'redis')
            redis_port = getattr(settings, 'CHANNEL_REDIS_PORT', 6379)
            redis_conn = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            redis_conn.ping()
            self.stdout.write(self.style.SUCCESS('✅ Redis connection healthy'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Redis is not accessible: {e}'))
            return
        
        # Initialize VPN loader (reused for both loading and testing)
        loader = VPNNetworkLoader(redis_conn=redis_conn)
        
        # Check if VPN networks are loaded (using loader's exported constant)
        vpn_count = redis_conn.scard(REDIS_VPN_KEY)
        if vpn_count == 0:
            if load_first:
                self.stdout.write(self.style.WARNING('VPN networks not found in Redis. Loading...'))
                success, count, message = loader.load_vpn_networks()
                if success:
                    self.stdout.write(self.style.SUCCESS(f'{message}'))
                else:
                    self.stdout.write(self.style.ERROR(f'{message}'))
                    return
            else:
                self.stdout.write(self.style.ERROR('VPN networks not found in Redis. Use --load-first to load them.'))
                return
        else:
            self.stdout.write(self.style.SUCCESS(f'Found {vpn_count:,} VPN networks in Redis'))
        
        # Test cases: (IP, expected_result, description)
        test_cases = [
            ('2.58.36.11', True, 'Should be in VPN network 2.58.36.0/22'),
            ('5.104.79.9', True, 'Should be in VPN network 5.104.78.0/23'),
            ('8.8.8.8', False, 'Should NOT be VPN (Google DNS)'),
            ('1.1.1.1', False, 'Should NOT be VPN (Cloudflare DNS)'),
        ]
        
        # If specific IP provided, test only that
        if test_ip:
            # Find matching test case or create new one
            test_cases = [(test_ip, None, f'Custom test for {test_ip}')]
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('VPN IP Lookup Test Results'))
        self.stdout.write('='*70 + '\n')
        
        all_passed = True
        total_time = 0
        
        for ip, expected, description in test_cases:
            try:
                # Time the lookup
                start_time = time.time()
                result = loader.verify_vpn_ip(ip)
                elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
                total_time += elapsed
                
                # Determine if test passed
                if expected is not None:
                    passed = (result == expected)
                    status = 'PASS' if passed else 'FAIL'
                    status_style = self.style.SUCCESS if passed else self.style.ERROR
                else:
                    passed = True  # No expected value, just show result
                    status = 'INFO'
                    status_style = self.style.SUCCESS
                
                if not passed:
                    all_passed = False
                
                # Display result
                self.stdout.write(f'{status_style(status)} | {ip:15} | VPN: {str(result):5} | {elapsed:6.2f}ms')
                self.stdout.write(f'         Description: {description}')
                
                if expected is not None and not passed:
                    self.stdout.write(self.style.ERROR(
                        f'         Expected: {expected}, Got: {result}'
                    ))
                
                self.stdout.write('')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'ERROR | {ip:15} | Exception: {e}'))
                all_passed = False
                self.stdout.write('')
        
        # Summary
        self.stdout.write('='*70)
        if all_passed:
            self.stdout.write(self.style.SUCCESS(f'✅ All tests passed! (Total time: {total_time:.2f}ms)'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ Some tests failed! (Total time: {total_time:.2f}ms)'))
        self.stdout.write('='*70)
        
        # Performance info
        if len(test_cases) > 0:
            avg_time = total_time / len(test_cases)
            self.stdout.write(f'\nAverage lookup time: {avg_time:.2f}ms per IP')
            cache_status = loader.get_cache_status()
            self.stdout.write(f'Cache status: {"Loaded" if cache_status["is_loaded"] else "Not loaded"}')
            if cache_status["is_loaded"]:
                self.stdout.write(f'Cached networks: {cache_status["count"]:,}')


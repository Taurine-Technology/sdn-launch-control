"""
Django management command to seed the database with test data for device monitoring.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from network_device.models import NetworkDevice
from device_monitoring.models import DevicePingStats, DeviceStats, PortUtilizationStats
from account.models import Account


class Command(BaseCommand):
    help = 'Seed the database with test data for device monitoring'

    def add_arguments(self, parser):
        parser.add_argument(
            '--devices',
            type=int,
            default=10,
            help='Number of test devices to create (default: 10)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=2,
            help='Number of days of historical data to generate (default: 2)'
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=None,
            help='Number of hours of historical data (overrides --days if specified)'
        )

    def handle(self, *args, **options):
        num_devices = options['devices']
        days = options['days']
        hours = options['hours']
        
        # Calculate timeframe
        if hours:
            timeframe_delta = timedelta(hours=hours)
            timeframe_str = f'{hours} hours'
        else:
            timeframe_delta = timedelta(days=days)
            timeframe_str = f'{days} days'
        
        self.stdout.write(f'Creating {num_devices} test devices with {timeframe_str} of data...')
        
        # Get or create a test account
        account, created = Account.objects.get_or_create(
            username='test_user',
            defaults={'name': 'Test User', 'surname': 'Test'}
        )
        
        if created:
            self.stdout.write('Created test account')
        
        # Create test devices
        devices = []
        for i in range(num_devices):
            device_type = random.choice(['switch', 'server', 'access_point', 'controller'])
            device_name = f"Test {device_type.title()} {i+1}"
            ip_address = f"192.168.1.{100 + i}"
            mac_address = f"00:1A:2B:3C:4D:{i:02X}"
            
            device, created = NetworkDevice.objects.get_or_create(
                mac_address=mac_address,
                defaults={
                    'account': account,
                    'name': device_name,
                    'device_type': device_type,
                    'ip_address': ip_address,
                    'is_ping_target': random.random() < 0.8,  # 80% of devices are monitored
                    'number_of_ports': random.randint(4, 48),
                    'verified': True
                }
            )
            devices.append(device)
            
            if created:
                self.stdout.write(f'Created device: {device_name} ({ip_address})')
        
        # Generate historical ping data
        self.stdout.write('Generating historical ping data...')
        end_time = timezone.now()
        start_time = end_time - timeframe_delta
        
        for device in devices:
            if not device.is_ping_target:
                continue
            
            # Assign a reliability profile to each device
            # These profiles determine overall uptime and how often/long downtimes occur
            reliability_weights = [0.5, 0.3, 0.15, 0.05]  # 50% highly reliable, 30% reliable, 15% normal, 5% unreliable
            device_reliability = random.choices(
                [
                    {'name': 'highly_reliable', 'target_uptime': 0.999, 'downtime_events': 1, 'downtime_minutes': 2},   # 99.9% uptime, 1 outage of 2min
                    {'name': 'reliable', 'target_uptime': 0.985, 'downtime_events': 2, 'downtime_minutes': 5},          # 98.5% uptime, 2 outages of 5min each
                    {'name': 'normal', 'target_uptime': 0.95, 'downtime_events': 3, 'downtime_minutes': 12},            # 95% uptime, 3 outages of 12min each
                    {'name': 'unreliable', 'target_uptime': 0.88, 'downtime_events': 5, 'downtime_minutes': 20},        # 88% uptime, 5 outages of 20min each
                ],
                weights=reliability_weights
            )[0]
            
            # Pre-schedule specific downtime events at random times during the period
            total_minutes = int((end_time - start_time).total_seconds() / 60)
            downtime_periods = []
            
            for _ in range(device_reliability['downtime_events']):
                # Random start time for this downtime
                random_offset = random.randint(0, total_minutes - device_reliability['downtime_minutes'])
                downtime_start = start_time + timedelta(minutes=random_offset)
                downtime_end = downtime_start + timedelta(minutes=device_reliability['downtime_minutes'])
                downtime_periods.append((downtime_start, downtime_end))
            
            # Sort downtime periods by start time
            downtime_periods.sort(key=lambda x: x[0])
            
            # Generate ping data
            current_time = start_time
            while current_time <= end_time:
                # Check if current time falls within any downtime period
                is_in_downtime = any(start <= current_time < end for start, end in downtime_periods)
                
                if is_in_downtime:
                    # Device is down during scheduled downtime
                    is_alive = False
                    successful_pings = random.choices([0, 1, 2], weights=[0.85, 0.10, 0.05])[0]
                else:
                    # Device is online - 99.9% success rate during normal operation
                    if random.random() < 0.999:
                        is_alive = True
                        successful_pings = 5
                    else:
                        # Very rare momentary blip
                        is_alive = True  # Still considered alive (3+ of 5 pings succeed)
                        successful_pings = random.choice([3, 4])
                
                DevicePingStats.objects.create(
                    device=device,
                    is_alive=is_alive,
                    successful_pings=successful_pings,
                    timestamp=current_time
                )
                
                # Move to next check (every 1 minute)
                current_time += timedelta(minutes=1)
        
        # Generate device stats (CPU, Memory, Disk)
        self.stdout.write('Generating device statistics...')
        for device in devices:
            if not device.is_ping_target:
                continue
                
            current_time = start_time
            while current_time <= end_time:
                # Simulate realistic system stats
                hour = current_time.hour
                is_business_hours = 8 <= hour <= 18
                
                # CPU usage (higher during business hours)
                base_cpu = 20 if is_business_hours else 10
                cpu_usage = base_cpu + random.uniform(0, 30)
                
                # Memory usage (more stable)
                memory_usage = 60 + random.uniform(-10, 20)
                
                # Disk usage (slowly increasing)
                days_elapsed = (current_time - start_time).days
                base_disk = 40 + (days_elapsed * 0.5)
                disk_usage = base_disk + random.uniform(-5, 5)
                
                DeviceStats.objects.create(
                    ip_address=device.ip_address,
                    cpu=cpu_usage,
                    memory=memory_usage,
                    disk=disk_usage,
                    timestamp=current_time
                )
                
                # Move to next measurement (every 15 minutes)
                current_time += timedelta(minutes=15)
        
        # Generate port utilization data for switches
        self.stdout.write('Generating port utilization data...')
        for device in devices:
            if device.device_type != 'switch' or not device.is_ping_target:
                continue
                
            # Generate data for some ports
            num_ports = min(device.number_of_ports or 8, 8)
            for port_num in range(1, num_ports + 1):
                port_name = f"eth{port_num}"
                
                current_time = start_time
                while current_time <= end_time:
                    # Simulate realistic port utilization
                    hour = current_time.hour
                    is_business_hours = 8 <= hour <= 18
                    
                    # Base throughput (higher during business hours)
                    base_throughput = 100 if is_business_hours else 20
                    throughput = base_throughput + random.uniform(0, 200)
                    
                    # Utilization percentage
                    utilization = min(throughput / 1000 * 100, 100)  # Assume 1Gbps link
                    
                    # Generate byte deltas
                    duration_seconds = 300  # 5 minutes
                    rx_bytes = int(throughput * 1000000 / 8 * duration_seconds / 1000000)  # Convert to MB
                    tx_bytes = int(rx_bytes * random.uniform(0.8, 1.2))
                    
                    PortUtilizationStats.objects.create(
                        ip_address=device.ip_address,
                        port_name=port_name,
                        throughput_mbps=throughput,
                        utilization_percent=utilization,
                        rx_bytes_diff=rx_bytes,
                        tx_bytes_diff=tx_bytes,
                        duration_diff=duration_seconds,
                        timestamp=current_time
                    )
                    
                    # Move to next measurement (every 5 minutes)
                    current_time += timedelta(minutes=5)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(devices)} devices with {timeframe_str} of test data!'
            )
        )
        
        # Print summary
        total_pings = DevicePingStats.objects.count()
        total_stats = DeviceStats.objects.count()
        total_port_stats = PortUtilizationStats.objects.count()
        
        self.stdout.write(f'Total ping records: {total_pings}')
        self.stdout.write(f'Total device stats: {total_stats}')
        self.stdout.write(f'Total port stats: {total_port_stats}')

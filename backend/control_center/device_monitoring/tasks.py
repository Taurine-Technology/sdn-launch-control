"""
Celery tasks for device health monitoring
"""
from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.utils import timezone
from datetime import timedelta
import logging

from .models import DeviceStats, DeviceHealthAlert, PortUtilizationStats, PortUtilizationAlert, DevicePingStats
from .utils import ping_device, ping_devices_with_fallback
from notification.models import Notification
from network_device.models import NetworkDevice

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task
def check_device_health():
    """
    Checks device health metrics and creates notifications for threshold violations.
    
    Thresholds:
    - CPU: Average > 90% over last 15 seconds (throttled to once per 60 seconds)
    - Memory: Average > 90% over last 15 seconds (throttled to once per 60 seconds)
    - Disk: Latest reading > 95% (throttled to once per hour)
    
    Notifications are throttled per device per metric to prevent spam.
    """
    try:
        # Get distinct device IPs that have recent stats
        one_hour_ago = timezone.now() - timedelta(hours=1)
        sixty_seconds_ago = timezone.now() - timedelta(seconds=60)
        fifteen_seconds_ago = timezone.now() - timedelta(seconds=15)
        
        # Query for CPU and memory averages over last 15 seconds using TimescaleDB
        # Use last(disk, timestamp) to get the most recent disk reading, not MAX
        query = """
            SELECT 
                ip_address,
                AVG(cpu) as avg_cpu,
                AVG(memory) as avg_memory,
                last(disk, timestamp) as latest_disk
            FROM device_monitoring_devicestats
            WHERE timestamp >= %s
            GROUP BY ip_address
        """
        
        with connection.cursor() as cursor:
            cursor.execute(query, [fifteen_seconds_ago])
            device_stats = cursor.fetchall()
        
        if not device_stats:
            logger.debug("No device stats found in last 15 seconds")
            return {"success": True, "message": "Device health check completed - no devices with recent stats"}
        
        
        # Fetch users once for all devices to avoid redundant queries
        users = User.objects.all()
        user_count = users.count()
        if user_count == 0:
            logger.warning("No users in system to notify!")
            return {"success": True, "message": "Device health check completed - no users to notify"}
        
        for ip_address, avg_cpu, avg_memory, latest_disk in device_stats:
            logger.debug(f"Device {ip_address}: CPU={avg_cpu:.2f}%, Memory={avg_memory:.2f}%, Disk={latest_disk:.2f}%")
            
            alerts_to_send = []
            now = timezone.now()
            
            # Lock and atomically update throttle timestamps to avoid race conditions
            with transaction.atomic():
                # Acquire row-level lock to prevent concurrent task runs from creating duplicates
                alert_record, _ = DeviceHealthAlert.objects.select_for_update().get_or_create(
                    ip_address=ip_address
                )
                
                # Check CPU threshold - Throttled to once per 60 seconds
                if avg_cpu > 90:
                    logger.debug(f"Device {ip_address}: CPU threshold exceeded - {avg_cpu:.2f}%")
                    if not alert_record.last_cpu_alert or alert_record.last_cpu_alert < sixty_seconds_ago:
                        alerts_to_send.append({
                            'type': 'cpu',
                            'message': f"Device {ip_address}: CPU usage averaged {avg_cpu:.2f}% over last 15 seconds"
                        })
                        alert_record.last_cpu_alert = now
                    else:
                        logger.debug(f"Device {ip_address}: CPU alert throttled (last sent: {alert_record.last_cpu_alert})")
                
                # Check Memory threshold - Throttled to once per 60 seconds
                if avg_memory > 90:
                    logger.debug(f"Device {ip_address}: Memory threshold exceeded - {avg_memory:.2f}%")
                    if not alert_record.last_memory_alert or alert_record.last_memory_alert < sixty_seconds_ago:
                        alerts_to_send.append({
                            'type': 'memory',
                            'message': f"Device {ip_address}: Memory usage averaged {avg_memory:.2f}% over last 15 seconds"
                        })
                        alert_record.last_memory_alert = now
                    else:
                        logger.debug(f"Device {ip_address}: Memory alert throttled (last sent: {alert_record.last_memory_alert})")
                
                # Check Disk threshold - Throttled to once per hour
                if latest_disk > 95:
                    logger.debug(f"Device {ip_address}: Disk threshold exceeded - {latest_disk:.2f}%")
                    if not alert_record.last_disk_alert or alert_record.last_disk_alert < one_hour_ago:
                        alerts_to_send.append({
                            'type': 'disk',
                            'message': f"Device {ip_address}: Disk usage is {latest_disk:.2f}%"
                        })
                        alert_record.last_disk_alert = now
                    else:
                        logger.debug(f"Device {ip_address}: Disk alert throttled (last sent: {alert_record.last_disk_alert})")
                
                # Persist throttle timestamps atomically only if alerts will be sent
                if alerts_to_send:
                    logger.debug(f"Device {ip_address}: {len(alerts_to_send)} alert(s) to send")
                    alert_record.save()
            
            # Create notifications outside the transaction to minimize lock duration
            if alerts_to_send:
                notifications_to_create = []
                
                for user in users:
                    for alert in alerts_to_send:
                        notifications_to_create.append(
                            Notification(
                                user=user,
                                message=alert['message'],
                                urgency='high',
                                type='DEVICE_RESOURCE',
                                notifier=None
                            )
                        )
                
                # Bulk create notifications for efficiency
                if notifications_to_create:
                    Notification.objects.bulk_create(notifications_to_create)
                    logger.debug(f"Created {len(notifications_to_create)} health notifications for device {ip_address}")
        
        return {"success": True, "message": "Device health check completed"}
    
    except Exception as e:
        logger.exception("Error in check_device_health")
        return {"success": False, "message": str(e)}


@shared_task
def check_port_utilization():
    """
    Checks port utilization metrics and creates notifications for threshold violations.
    
    Thresholds:
    - Utilization: Average > 85% over last 15 seconds (throttled to once per 30 seconds)
    - Urgency: medium for 85-95%, high for >95%
    - Missing link_speed: Warn users (throttled to once per hour)
    
    Uses TimescaleDB for efficient time-series aggregation.
    """
    try:
        # Calculate time thresholds
        thirty_seconds_ago = timezone.now() - timedelta(seconds=30)
        one_hour_ago = timezone.now() - timedelta(hours=1)
        fifteen_seconds_ago = timezone.now() - timedelta(seconds=15)
        
        # Query for ports exceeding 85% utilization over last 15 seconds
        utilization_query = """
            SELECT ip_address, port_name, 
                   AVG(utilization_percent) as avg_utilization,
                   AVG(throughput_mbps) as avg_throughput
            FROM device_monitoring_portutilizationstats
            WHERE timestamp >= %s
              AND utilization_percent IS NOT NULL
              AND utilization_percent > 0
            GROUP BY ip_address, port_name
            HAVING AVG(utilization_percent) > 85
            ORDER BY avg_utilization DESC
        """
        
        # Query for ports with missing link_speed (throughput > 0 but utilization = 0)
        missing_link_speed_query = """
            SELECT DISTINCT ip_address, port_name, AVG(throughput_mbps) as avg_throughput
            FROM device_monitoring_portutilizationstats
            WHERE timestamp >= %s
              AND utilization_percent = 0
              AND throughput_mbps > 0
            GROUP BY ip_address, port_name
        """
        
        with connection.cursor() as cursor:
            cursor.execute(utilization_query, [fifteen_seconds_ago])
            utilization_violations = cursor.fetchall()
            
            cursor.execute(missing_link_speed_query, [fifteen_seconds_ago])
            missing_link_speed_ports = cursor.fetchall()
        
        if not utilization_violations and not missing_link_speed_ports:
            return {"success": True, "message": "Port utilization check completed - no issues found"}
        
        # Get all users for notifications
        users = User.objects.all()
        user_count = users.count()
        if user_count == 0:
            logger.warning("No users in system to notify!")
            return {"success": True, "message": "Port utilization check completed - no users to notify"}
        
        now = timezone.now()
        notifications_to_create = []
        
        # Process utilization violations
        for ip_address, port_name, avg_utilization, avg_throughput in utilization_violations:
            logger.debug(f"Port {port_name} on {ip_address}: {avg_utilization:.2f}% utilized")
            
            with transaction.atomic():
                # Lock and check throttle for utilization alerts
                alert_record, _ = PortUtilizationAlert.objects.select_for_update().get_or_create(
                    ip_address=ip_address,
                    port_name=port_name
                )
                
                # Check if we can send an alert (30 second throttle)
                if (not alert_record.last_utilization_alert or 
                    alert_record.last_utilization_alert < thirty_seconds_ago):
                    
                    # Determine urgency based on utilization level
                    urgency = 'high' if avg_utilization > 95 else 'medium'
                    
                    message = (f"Port {port_name} on {ip_address}: "
                             f"{avg_utilization:.2f}% utilized ({avg_throughput:.2f} Mbps)")
                    
                    # Create notifications for all users
                    for user in users:
                        notifications_to_create.append(
                            Notification(
                                user=user,
                                message=message,
                                urgency=urgency,
                                type='DEVICE_RESOURCE',
                                notifier=None
                            )
                        )
                    
                    alert_record.last_utilization_alert = now
                    alert_record.save()
                    logger.debug(f"Created utilization alert for port {port_name} on {ip_address}")
                else:
                    logger.debug(f"Utilization alert throttled for port {port_name} on {ip_address}")
        
        # Process missing link_speed warnings
            with transaction.atomic():
                # Lock and check throttle for link_speed alerts (1 hour throttle)
                alert_record, _ = PortUtilizationAlert.objects.select_for_update().get_or_create(
                    ip_address=ip_address,
                    port_name=port_name
                )
                
                # Check if we can send a link_speed warning (1 hour throttle)
                if (not alert_record.last_null_link_speed_alert or 
                    alert_record.last_null_link_speed_alert < one_hour_ago):
                    
                    message = (f"Port {port_name} on {ip_address}: link_speed not configured "
                             f"(measuring {avg_throughput:.2f} Mbps throughput)")
                    
                    # Create notifications for all users
                    for user in users:
                        notifications_to_create.append(
                            Notification(
                                user=user,
                                message=message,
                                urgency='medium',
                                type='DEVICE_RESOURCE',
                                notifier=None
                            )
                        )
                    
                    alert_record.last_null_link_speed_alert = now
                    alert_record.save()
                    logger.debug(f"Created link_speed warning for port {port_name} on {ip_address}")
                else:
                    logger.debug(f"Link_speed warning throttled for port {port_name} on {ip_address}")
        
        # Bulk create all notifications
        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)
            logger.debug(f"Created {len(notifications_to_create)} port utilization notifications")
        
        return {"success": True, "message": "Port utilization check completed"}
    
    except Exception as e:
        logger.exception("Error in check_port_utilization")
        return {"success": False, "message": str(e)}


@shared_task
def ping_all_monitored_devices():
    """
    Ping all monitored devices using optimized batch processing.
    
    Uses fping's multi-host mode to ping multiple devices simultaneously,
    with fallback to individual pings if batch fails. Processes devices in
    batches of 10 for optimal performance.
    
    Runs every minute via Celery Beat.
    
    Sends 5 pings using fping. Device is considered alive if 3+ pings succeed.
    """
    try:
        devices = NetworkDevice.objects.filter(
            is_ping_target=True,
            ip_address__isnull=False
        )
        
        device_list = list(devices)
        logger.debug(f"Pinging {len(device_list)} monitored devices using batch mode")
        
        if not device_list:
            logger.debug("No devices to ping")
            return {
                'success': True,
                'devices_pinged': 0,
                'message': 'No devices to ping'
            }
        
        # Extract IP addresses and create device mapping
        ip_to_device = {}
        ip_addresses = []
        
        for device in device_list:
            if device.ip_address:
                ip_to_device[device.ip_address] = device
                ip_addresses.append(device.ip_address)
        
        if not ip_addresses:
            logger.warning("No valid IP addresses found")
            return {
                'success': True,
                'devices_pinged': 0,
                'message': 'No valid IP addresses found'
            }
        
        # Ping all devices using batch mode with fallback
        ping_results = ping_devices_with_fallback(ip_addresses, batch_size=10)
        
        # Create DevicePingStats records
        stats_to_create = []
        successful_pings = 0
        failed_pings = 0
        
        for ip_address, (is_alive, successful_count) in ping_results.items():
            if ip_address in ip_to_device:
                device = ip_to_device[ip_address]
                
                stats_to_create.append(
                    DevicePingStats(
                        device=device,
                        is_alive=is_alive,
                        successful_pings=successful_count
                    )
                )
                
                if is_alive:
                    successful_pings += 1
                else:
                    failed_pings += 1
                
                logger.debug(
                    f"Pinged {ip_address}: "
                    f"{successful_count}/5 successful, "
                    f"{'alive' if is_alive else 'down'}"
                )
            else:
                logger.warning(f"No device found for IP {ip_address}")
        
        # Bulk create all stats records
        if stats_to_create:
            DevicePingStats.objects.bulk_create(stats_to_create)
            logger.debug(
                f"Created {len(stats_to_create)} ping stats records: "
                f"{successful_pings} alive, {failed_pings} down"
            )
        
        return {
            'success': True,
            'devices_pinged': len(device_list),
            'alive_devices': successful_pings,
            'down_devices': failed_pings
        }
        
    except Exception as e:
        logger.exception("Error in ping_all_monitored_devices")
        return {
            'success': False,
            'message': str(e)
        }


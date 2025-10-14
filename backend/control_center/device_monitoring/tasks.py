"""
Celery tasks for device health monitoring
"""
from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.utils import timezone
from datetime import timedelta
import logging

from .models import DeviceStats, DeviceHealthAlert
from notification.models import Notification

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
        
        logger.info(f"Checking health for {len(device_stats)} device(s)")
        
        # Fetch users once for all devices to avoid redundant queries
        users = User.objects.all()
        user_count = users.count()
        if user_count == 0:
            logger.warning("No users in system to notify!")
            return {"success": True, "message": "Device health check completed - no users to notify"}
        logger.info(f"Found {user_count} user(s) to notify")
        
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
                    logger.info(f"Device {ip_address}: CPU threshold exceeded - {avg_cpu:.2f}%")
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
                    logger.info(f"Device {ip_address}: Memory threshold exceeded - {avg_memory:.2f}%")
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
                    logger.info(f"Device {ip_address}: Disk threshold exceeded - {latest_disk:.2f}%")
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
                    logger.info(f"Device {ip_address}: {len(alerts_to_send)} alert(s) to send")
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
                    logger.info(f"Created {len(notifications_to_create)} health notifications for device {ip_address}")
        
        return {"success": True, "message": "Device health check completed"}
    
    except Exception as e:
        logger.exception("Error in check_device_health")
        return {"success": False, "message": str(e)}


# File: tasks.py
# Copyright (C) 2025 Taurine Technology
#
# This file is part of the SDN Launch Control project.
#
# This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0),
# available at: https://www.gnu.org/licenses/agpl-3.0.en.html#license-text
#
# Contributions to this project are governed by a Contributor License Agreement (CLA).
# By submitting a contribution, contributors grant Taurine Technology exclusive rights to
# the contribution, including the right to relicense it under a different license
# at the copyright owner's discretion.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the GNU Affero General Public License for more details.
#
# For inquiries, contact Keegan White at keeganwhite@taurinetech.com.

"""
Celery tasks for SNMP device monitoring.

Provides two main tasks:
1. poll_single_snmp_device(device_id) - Poll a single device by ID
2. poll_all_snmp_devices() - Poll all active devices that are due for polling

These tasks integrate with the SNMP utilities to collect metrics from network
devices and store them in TimescaleDB.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from .models import SNMPDevice
from .utilities import poll_snmp_device

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def poll_single_snmp_device(self, device_id: int) -> dict:
    """
    Poll a single SNMP device by its database ID.
    
    This task looks up the device by ID and calls the poll_snmp_device utility
    function to collect metrics via SNMP and store them in the database.
    
    Args:
        device_id: The primary key of the SNMPDevice to poll.
        
    Returns:
        dict: Result containing:
            - success (bool): Whether polling succeeded
            - message (str): Description of the result
            - device_id (int): The device ID that was polled
            - device_name (str): The device name (if found)
            
    Raises:
        Retry: If polling fails and retries are available
    """
    try:
        # Look up the device
        try:
            device = SNMPDevice.objects.get(pk=device_id)
        except SNMPDevice.DoesNotExist:
            logger.error(f"SNMPDevice with id={device_id} not found")
            return {
                "success": False,
                "message": f"Device with id={device_id} not found",
                "device_id": device_id,
                "device_name": None
            }
        
        # Check if device is active
        if not device.is_active:
            logger.warning(f"Device {device.name} ({device_id}) is not active, skipping poll")
            return {
                "success": False,
                "message": f"Device {device.name} is not active",
                "device_id": device_id,
                "device_name": device.name
            }
        
        logger.info(f"Starting SNMP poll task for device {device.name} ({device.ip_address})")
        
        # Call the polling utility
        success, error_message = poll_snmp_device(device)
        
        if success:
            logger.info(f"Successfully polled SNMP device {device.name}")
            return {
                "success": True,
                "message": f"Successfully polled device {device.name}",
                "device_id": device_id,
                "device_name": device.name
            }
        else:
            logger.warning(f"Failed to poll SNMP device {device.name}: {error_message}")
            
            # Retry if we have retries left
            if self.request.retries < self.max_retries:
                logger.info(f"Retrying poll for device {device.name} (attempt {self.request.retries + 1}/{self.max_retries})")
                raise self.retry(exc=Exception(error_message))
            
            return {
                "success": False,
                "message": f"Failed to poll device {device.name}: {error_message}",
                "device_id": device_id,
                "device_name": device.name
            }
            
    except self.MaxRetriesExceededError:
        logger.error(f"Max retries exceeded for device {device_id}")
        return {
            "success": False,
            "message": f"Max retries exceeded for device {device_id}",
            "device_id": device_id,
            "device_name": None
        }
    except Exception as e:
        logger.exception(f"Unexpected error polling SNMP device {device_id}")
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "device_id": device_id,
            "device_name": None
        }


@shared_task
def poll_all_snmp_devices(inline: bool = False) -> dict:
    """
    Poll all active SNMP devices that are due for polling.
    
    This task filters devices by:
    1. is_active=True - Only poll devices that are enabled
    2. Polling interval check - Only poll if enough time has passed since last_poll_attempt
    
    For each due device, it either:
    - Calls poll_snmp_device directly (if inline=True)
    - Schedules poll_single_snmp_device.delay() (if inline=False, default)
    
    Args:
        inline: If True, poll devices directly in this task.
                If False (default), schedule separate tasks for each device.
                Use inline=True for testing or when running without Celery workers.
                
    Returns:
        dict: Result containing:
            - success (bool): Whether the task completed without errors
            - message (str): Summary of the operation
            - total_active (int): Number of active devices
            - devices_due (int): Number of devices that were due for polling
            - devices_polled (int): Number of devices actually polled/scheduled
            - devices_skipped (int): Number of devices skipped (not due yet)
            - results (list): Per-device results (only if inline=True)
    """
    try:
        now = timezone.now()
        
        # Get all active devices
        active_devices = SNMPDevice.objects.filter(is_active=True)
        total_active = active_devices.count()
        
        if total_active == 0:
            logger.info("No active SNMP devices to poll")
            return {
                "success": True,
                "message": "No active SNMP devices found",
                "total_active": 0,
                "devices_due": 0,
                "devices_polled": 0,
                "devices_skipped": 0
            }
        
        logger.info(f"Found {total_active} active SNMP device(s)")
        
        devices_due = 0
        devices_polled = 0
        devices_skipped = 0
        results = []
        
        for device in active_devices:
            # Check if device is due for polling
            is_due = False
            
            if device.last_poll_attempt is None:
                # Never polled before, definitely due
                is_due = True
                logger.debug(f"Device {device.name} has never been polled, due now")
            else:
                # Check if polling interval has elapsed
                time_since_last_poll = (now - device.last_poll_attempt).total_seconds()
                if time_since_last_poll >= device.polling_interval:
                    is_due = True
                    logger.debug(
                        f"Device {device.name}: {time_since_last_poll:.1f}s since last poll "
                        f"(interval: {device.polling_interval}s), due now"
                    )
                else:
                    logger.debug(
                        f"Device {device.name}: {time_since_last_poll:.1f}s since last poll "
                        f"(interval: {device.polling_interval}s), skipping"
                    )
            
            if is_due:
                devices_due += 1
                
                if inline:
                    # Poll directly in this task
                    logger.info(f"Polling device {device.name} inline")
                    success, error_message = poll_snmp_device(device)
                    devices_polled += 1
                    results.append({
                        "device_id": device.id,
                        "device_name": device.name,
                        "success": success,
                        "error": error_message
                    })
                else:
                    # Schedule as separate task
                    logger.info(f"Scheduling poll task for device {device.name}")
                    poll_single_snmp_device.delay(device.id)
                    devices_polled += 1
            else:
                devices_skipped += 1
        
        message = (
            f"Processed {total_active} active device(s): "
            f"{devices_polled} polled/scheduled, {devices_skipped} skipped (not due)"
        )
        logger.info(message)
        
        result = {
            "success": True,
            "message": message,
            "total_active": total_active,
            "devices_due": devices_due,
            "devices_polled": devices_polled,
            "devices_skipped": devices_skipped
        }
        
        if inline:
            result["results"] = results
            
        return result
        
    except Exception as e:
        logger.exception("Error in poll_all_snmp_devices")
        return {
            "success": False,
            "message": f"Error polling devices: {str(e)}",
            "total_active": 0,
            "devices_due": 0,
            "devices_polled": 0,
            "devices_skipped": 0
        }


@shared_task
def check_snmp_device_health() -> dict:
    """
    Check SNMP device health and create alerts for issues.
    
    Checks for:
    1. Devices with high consecutive failures (connection issues)
    2. Devices that haven't been polled in a long time
    
    This task is intended to run periodically (e.g., every 5 minutes) to
    identify devices that may need attention.
    
    Returns:
        dict: Result containing health check summary
    """
    try:
        now = timezone.now()
        
        # Check for devices with high consecutive failures
        failure_threshold = 5
        devices_with_failures = SNMPDevice.objects.filter(
            is_active=True,
            consecutive_failures__gte=failure_threshold
        )
        
        failing_devices = []
        for device in devices_with_failures:
            failing_devices.append({
                "id": device.id,
                "name": device.name,
                "ip_address": device.ip_address,
                "consecutive_failures": device.consecutive_failures,
                "last_successful_poll": device.last_successful_poll.isoformat() if device.last_successful_poll else None
            })
            logger.warning(
                f"Device {device.name} ({device.ip_address}) has {device.consecutive_failures} "
                f"consecutive failures"
            )
        
        # Check for devices not polled in a long time (10x their polling interval)
        stale_devices = []
        active_devices = SNMPDevice.objects.filter(is_active=True)
        
        for device in active_devices:
            if device.last_poll_attempt:
                stale_threshold = timedelta(seconds=device.polling_interval * 10)
                if (now - device.last_poll_attempt) > stale_threshold:
                    stale_devices.append({
                        "id": device.id,
                        "name": device.name,
                        "ip_address": device.ip_address,
                        "last_poll_attempt": device.last_poll_attempt.isoformat(),
                        "polling_interval": device.polling_interval
                    })
                    logger.warning(
                        f"Device {device.name} hasn't been polled since {device.last_poll_attempt}"
                    )
        
        return {
            "success": True,
            "message": f"Health check complete: {len(failing_devices)} failing, {len(stale_devices)} stale",
            "failing_devices": failing_devices,
            "stale_devices": stale_devices,
            "total_active": active_devices.count()
        }
        
    except Exception as e:
        logger.exception("Error in check_snmp_device_health")
        return {
            "success": False,
            "message": f"Error checking device health: {str(e)}"
        }


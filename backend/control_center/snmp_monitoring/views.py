# File: views.py
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
REST API ViewSets for SNMP monitoring.

Provides:
- SNMPDeviceViewSet: Full CRUD + manual poll trigger
- SNMPMetricsViewSet: Read-only metrics with time filtering and aggregation
- SNMPInterfaceStatsViewSet: Read-only interface stats with time filtering
"""

import logging
from django.db import connection
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import SNMPDevice, SNMPMetrics, SNMPInterfaceStats
from .serializers import (
    SNMPDeviceSerializer,
    SNMPDeviceListSerializer,
    SNMPMetricsSerializer,
    SNMPInterfaceStatsSerializer,
)
from .tasks import poll_single_snmp_device

logger = logging.getLogger(__name__)


class SNMPDeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing SNMP devices.
    
    Provides full CRUD operations plus a manual poll trigger.
    
    Endpoints:
    - GET /snmp-devices/ - List all SNMP devices
    - POST /snmp-devices/ - Create a new SNMP device
    - GET /snmp-devices/{id}/ - Retrieve a specific device
    - PUT /snmp-devices/{id}/ - Update a device
    - PATCH /snmp-devices/{id}/ - Partial update a device
    - DELETE /snmp-devices/{id}/ - Delete a device
    - POST /snmp-devices/{id}/poll/ - Trigger manual SNMP poll
    
    Query Parameters:
    - is_active (optional): Filter by active status (true/false)
    - vendor (optional): Filter by vendor (e.g., "mikrotik", "ubiquiti")
    - ip_address (optional): Filter by IP address
    """
    permission_classes = [IsAuthenticated]
    queryset = SNMPDevice.objects.all()
    
    def get_serializer_class(self):
        """Use lightweight serializer for list actions."""
        if self.action == 'list':
            return SNMPDeviceListSerializer
        return SNMPDeviceSerializer
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = SNMPDevice.objects.all().order_by('-created_at')
        
        # Filter by is_active
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by vendor
        vendor = self.request.query_params.get('vendor')
        if vendor:
            queryset = queryset.filter(vendor=vendor)
        
        # Filter by IP address
        ip_address = self.request.query_params.get('ip_address')
        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)
        
        return queryset
    
    @action(detail=True, methods=['post'], url_path='poll')
    def poll(self, request, pk=None):
        """
        Trigger a manual SNMP poll for this device.
        
        This schedules an asynchronous Celery task to poll the device.
        The task will collect metrics and interface statistics via SNMP
        and store them in the database.
        
        Returns:
            - task_id: The Celery task ID for tracking
            - message: Status message
            
        Example:
            POST /api/v1/snmp-monitoring/snmp-devices/1/poll/
            
        Response:
            {
                "status": "scheduled",
                "message": "SNMP poll scheduled for device 'MikroTik Router'",
                "task_id": "abc123-...",
                "device_id": 1
            }
        """
        device = self.get_object()
        
        if not device.is_active:
            return Response(
                {
                    "status": "error",
                    "message": f"Device '{device.name}' is not active. Enable it first.",
                    "device_id": device.id
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Schedule the polling task
        try:
            task = poll_single_snmp_device.delay(device.id)
            logger.info(f"Scheduled SNMP poll for device {device.name} (task_id={task.id})")
            
            return Response({
                "status": "scheduled",
                "message": f"SNMP poll scheduled for device '{device.name}'",
                "task_id": str(task.id),
                "device_id": device.id
            })
        except Exception as e:
            logger.exception(f"Failed to schedule SNMP poll for device {device.id}")
            return Response(
                {
                    "status": "error",
                    "message": f"Failed to schedule poll: {str(e)}",
                    "device_id": device.id
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='poll-all')
    def poll_all(self, request):
        """
        Trigger SNMP polling for all active devices.
        
        This schedules the poll_all_snmp_devices task which will
        poll all active devices that are due for polling.
        
        Returns:
            - message: Status message
            - active_devices: Count of active devices
        """
        from .tasks import poll_all_snmp_devices
        
        try:
            active_count = SNMPDevice.objects.filter(is_active=True).count()
            
            if active_count == 0:
                return Response({
                    "status": "skipped",
                    "message": "No active SNMP devices to poll",
                    "active_devices": 0
                })
            
            task = poll_all_snmp_devices.delay()
            logger.info(f"Scheduled poll for all active SNMP devices (task_id={task.id})")
            
            return Response({
                "status": "scheduled",
                "message": f"Scheduled polling for {active_count} active device(s)",
                "task_id": str(task.id),
                "active_devices": active_count
            })
        except Exception as e:
            logger.exception("Failed to schedule poll for all devices")
            return Response(
                {
                    "status": "error",
                    "message": f"Failed to schedule poll: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SNMPMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for querying SNMP device metrics.
    
    Read-only access to CPU, memory, disk usage, and uptime data.
    Supports time filtering and TimescaleDB aggregation.
    
    Endpoints:
    - GET /snmp-metrics/ - List metrics with filters
    - GET /snmp-metrics/{id}/ - Retrieve specific metric record
    - GET /snmp-metrics/aggregate/ - Time-bucketed aggregates
    
    Query Parameters:
    - device_id (recommended): Filter by SNMP device ID
    - ip_address (optional): Filter by device IP address
    - start_time (optional): ISO 8601 format (e.g., "2025-01-01T00:00:00Z")
    - end_time (optional): ISO 8601 format (default: now)
    - hours (optional): Shortcut for last N hours
    - days (optional): Shortcut for last N days
    - limit (optional): Max records to return (default: 1000, max: 10000)
    """
    serializer_class = SNMPMetricsSerializer
    permission_classes = [IsAuthenticated]
    
    MAX_LIMIT = 10000
    DEFAULT_LIMIT = 1000
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = SNMPMetrics.objects.all().select_related('device')
        
        # Filter by device_id
        device_id = self.request.query_params.get('device_id')
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        
        # Filter by IP address
        ip_address = self.request.query_params.get('ip_address')
        if ip_address:
            queryset = queryset.filter(device__ip_address=ip_address)
        
        # Time filters
        queryset = self._apply_time_filters(queryset)
        
        # Order by timestamp descending (newest first)
        return queryset.order_by('-timestamp')
    
    def _apply_time_filters(self, queryset):
        """Apply time-based filters from query parameters."""
        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')
        hours = self.request.query_params.get('hours')
        days = self.request.query_params.get('days')
        
        # Handle shortcuts
        if hours:
            try:
                hours_float = float(hours)
                start_time = (timezone.now() - timezone.timedelta(hours=hours_float)).isoformat()
            except ValueError:
                pass
        
        if days:
            try:
                days_int = int(days)
                start_time = (timezone.now() - timezone.timedelta(days=days_int)).isoformat()
            except ValueError:
                pass
        
        # Apply start_time
        if start_time:
            try:
                start_dt = parse_datetime(start_time)
                if start_dt:
                    queryset = queryset.filter(timestamp__gte=start_dt)
            except ValueError:
                pass
        
        # Apply end_time
        if end_time:
            try:
                end_dt = parse_datetime(end_time)
                if end_dt:
                    queryset = queryset.filter(timestamp__lte=end_dt)
            except ValueError:
                pass
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Override list to add pagination and metadata."""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Apply limit
        limit_param = request.query_params.get('limit')
        try:
            limit = min(int(limit_param), self.MAX_LIMIT) if limit_param else self.DEFAULT_LIMIT
        except ValueError:
            limit = self.DEFAULT_LIMIT
        
        total_count = queryset.count()
        queryset = queryset[:limit]
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'data': serializer.data,
            'metadata': {
                'count': len(serializer.data),
                'total_available': total_count,
                'limit_applied': limit,
            }
        })
    
    @action(detail=False, methods=['get'], url_path='aggregate')
    def aggregate(self, request):
        """
        Aggregate metrics using TimescaleDB time_bucket function.
        
        Returns time-bucketed averages for charting device resource usage.
        
        Query Parameters:
        - device_id (required): SNMP device ID
        - start_time, end_time, hours, days: Time filters
        - interval (optional): Time bucket size (default: '5 minutes')
          Valid: '1 minute', '5 minutes', '15 minutes', '1 hour', '1 day'
        
        Returns:
        {
            "data": [
                {
                    "bucket_time": "2025-01-01T00:00:00Z",
                    "cpu_avg": 45.2,
                    "cpu_max": 78.5,
                    "memory_avg": 62.1,
                    "memory_max": 68.3,
                    "disk_avg": 55.0,
                    "disk_max": 55.2,
                    "uptime_avg": 86400
                },
                ...
            ],
            "metadata": {
                "bucket": "5 minutes",
                "device_id": 1,
                "count": 288
            }
        }
        """
        device_id = request.query_params.get('device_id')
        if not device_id:
            return Response(
                {"error": "device_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate device exists
        if not SNMPDevice.objects.filter(id=device_id).exists():
            return Response(
                {"error": f"Device with id={device_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get time parameters
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        interval = request.query_params.get('interval', '5 minutes')
        hours = request.query_params.get('hours')
        days = request.query_params.get('days')
        
        # Handle shortcuts
        if hours:
            try:
                hours_float = float(hours)
                start_time = (timezone.now() - timezone.timedelta(hours=hours_float)).isoformat()
            except ValueError:
                pass
        
        if days:
            try:
                days_int = int(days)
                start_time = (timezone.now() - timezone.timedelta(days=days_int)).isoformat()
            except ValueError:
                pass
        
        # Validate interval
        valid_intervals = ['1 minute', '5 minutes', '15 minutes', '1 hour', '1 day']
        if interval not in valid_intervals:
            return Response(
                {"error": f"Invalid interval. Must be one of: {valid_intervals}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build query
        where_conditions = ["device_id = %s"]
        params = [device_id]
        
        if start_time:
            try:
                start_dt = parse_datetime(start_time)
                if start_dt:
                    where_conditions.append("timestamp >= %s")
                    params.append(start_dt)
            except ValueError:
                return Response(
                    {"error": "Invalid start_time format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if end_time:
            try:
                end_dt = parse_datetime(end_time)
                if end_dt:
                    where_conditions.append("timestamp <= %s")
                    params.append(end_dt)
            except ValueError:
                return Response(
                    {"error": "Invalid end_time format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Default to last 24 hours if no time range specified
        if not start_time and not end_time and not hours and not days:
            where_conditions.append("timestamp >= %s")
            params.append(timezone.now() - timezone.timedelta(days=1))
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
            SELECT 
                time_bucket(%s::interval, timestamp) AS bucket_time,
                AVG(cpu_usage) AS cpu_avg,
                MAX(cpu_usage) AS cpu_max,
                AVG(memory_usage) AS memory_avg,
                MAX(memory_usage) AS memory_max,
                AVG(disk_usage) AS disk_avg,
                MAX(disk_usage) AS disk_max,
                AVG(uptime_seconds) AS uptime_avg
            FROM snmp_monitoring_snmpmetrics
            WHERE {where_clause}
            GROUP BY bucket_time
            ORDER BY bucket_time ASC
        """
        
        params = [interval] + params
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'bucket_time': row[0],
                    'cpu_avg': float(row[1]) if row[1] is not None else None,
                    'cpu_max': float(row[2]) if row[2] is not None else None,
                    'memory_avg': float(row[3]) if row[3] is not None else None,
                    'memory_max': float(row[4]) if row[4] is not None else None,
                    'disk_avg': float(row[5]) if row[5] is not None else None,
                    'disk_max': float(row[6]) if row[6] is not None else None,
                    'uptime_avg': int(row[7]) if row[7] is not None else None,
                })
            
            return Response({
                'data': results,
                'metadata': {
                    'bucket': interval,
                    'device_id': int(device_id),
                    'count': len(results)
                }
            })
            
        except Exception as e:
            logger.exception("Error in SNMP metrics aggregation")
            return Response(
                {"error": f"Database error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SNMPInterfaceStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for querying SNMP interface statistics.
    
    Read-only access to per-interface bytes, packets, errors, and throughput.
    Supports time filtering and TimescaleDB aggregation.
    
    Endpoints:
    - GET /snmp-interface-stats/ - List interface stats with filters
    - GET /snmp-interface-stats/{id}/ - Retrieve specific stat record
    - GET /snmp-interface-stats/aggregate/ - Time-bucketed aggregates
    
    Query Parameters:
    - device_id (recommended): Filter by SNMP device ID
    - ip_address (optional): Filter by device IP address
    - interface_name (optional): Filter by interface name
    - start_time (optional): ISO 8601 format
    - end_time (optional): ISO 8601 format
    - hours (optional): Shortcut for last N hours
    - days (optional): Shortcut for last N days
    - limit (optional): Max records to return
    """
    serializer_class = SNMPInterfaceStatsSerializer
    permission_classes = [IsAuthenticated]
    
    MAX_LIMIT = 10000
    DEFAULT_LIMIT = 1000
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = SNMPInterfaceStats.objects.all().select_related('device')
        
        # Filter by device_id
        device_id = self.request.query_params.get('device_id')
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        
        # Filter by IP address
        ip_address = self.request.query_params.get('ip_address')
        if ip_address:
            queryset = queryset.filter(device__ip_address=ip_address)
        
        # Filter by interface name
        interface_name = self.request.query_params.get('interface_name')
        if interface_name:
            queryset = queryset.filter(interface_name=interface_name)
        
        # Time filters
        queryset = self._apply_time_filters(queryset)
        
        return queryset.order_by('-timestamp')
    
    def _apply_time_filters(self, queryset):
        """Apply time-based filters from query parameters."""
        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')
        hours = self.request.query_params.get('hours')
        days = self.request.query_params.get('days')
        
        if hours:
            try:
                hours_float = float(hours)
                start_time = (timezone.now() - timezone.timedelta(hours=hours_float)).isoformat()
            except ValueError:
                pass
        
        if days:
            try:
                days_int = int(days)
                start_time = (timezone.now() - timezone.timedelta(days=days_int)).isoformat()
            except ValueError:
                pass
        
        if start_time:
            try:
                start_dt = parse_datetime(start_time)
                if start_dt:
                    queryset = queryset.filter(timestamp__gte=start_dt)
            except ValueError:
                pass
        
        if end_time:
            try:
                end_dt = parse_datetime(end_time)
                if end_dt:
                    queryset = queryset.filter(timestamp__lte=end_dt)
            except ValueError:
                pass
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Override list to add pagination and metadata."""
        queryset = self.filter_queryset(self.get_queryset())
        
        limit_param = request.query_params.get('limit')
        try:
            limit = min(int(limit_param), self.MAX_LIMIT) if limit_param else self.DEFAULT_LIMIT
        except ValueError:
            limit = self.DEFAULT_LIMIT
        
        total_count = queryset.count()
        queryset = queryset[:limit]
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'data': serializer.data,
            'metadata': {
                'count': len(serializer.data),
                'total_available': total_count,
                'limit_applied': limit,
            }
        })
    
    @action(detail=False, methods=['get'], url_path='aggregate')
    def aggregate(self, request):
        """
        Aggregate interface stats using TimescaleDB time_bucket function.
        
        Returns time-bucketed data for charting interface throughput.
        
        Query Parameters:
        - device_id (required): SNMP device ID
        - interface_name (optional): Filter by specific interface
        - start_time, end_time, hours, days: Time filters
        - interval (optional): Time bucket size (default: '5 minutes')
        
        Returns:
        {
            "aggregated_data": [
                {
                    "bucket_time": "2025-01-01T00:00:00Z",
                    "interface_name": "eth0",
                    "bytes_in_total": 1234567890,
                    "bytes_out_total": 987654321,
                    "packets_in_total": 123456,
                    "packets_out_total": 98765,
                    "errors_in_total": 0,
                    "errors_out_total": 0
                },
                ...
            ],
            "metadata": {...}
        }
        """
        device_id = request.query_params.get('device_id')
        if not device_id:
            return Response(
                {"error": "device_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not SNMPDevice.objects.filter(id=device_id).exists():
            return Response(
                {"error": f"Device with id={device_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        interface_name = request.query_params.get('interface_name')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        interval = request.query_params.get('interval', '5 minutes')
        hours = request.query_params.get('hours')
        days = request.query_params.get('days')
        
        if hours:
            try:
                hours_float = float(hours)
                start_time = (timezone.now() - timezone.timedelta(hours=hours_float)).isoformat()
            except ValueError:
                pass
        
        if days:
            try:
                days_int = int(days)
                start_time = (timezone.now() - timezone.timedelta(days=days_int)).isoformat()
            except ValueError:
                pass
        
        valid_intervals = ['1 minute', '5 minutes', '15 minutes', '1 hour', '1 day']
        if interval not in valid_intervals:
            return Response(
                {"error": f"Invalid interval. Must be one of: {valid_intervals}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        where_conditions = ["device_id = %s"]
        params = [device_id]
        
        if interface_name:
            where_conditions.append("interface_name = %s")
            params.append(interface_name)
        
        if start_time:
            try:
                start_dt = parse_datetime(start_time)
                if start_dt:
                    where_conditions.append("timestamp >= %s")
                    params.append(start_dt)
            except ValueError:
                return Response(
                    {"error": "Invalid start_time format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if end_time:
            try:
                end_dt = parse_datetime(end_time)
                if end_dt:
                    where_conditions.append("timestamp <= %s")
                    params.append(end_dt)
            except ValueError:
                return Response(
                    {"error": "Invalid end_time format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if not start_time and not end_time and not hours and not days:
            where_conditions.append("timestamp >= %s")
            params.append(timezone.now() - timezone.timedelta(days=1))
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
            SELECT 
                time_bucket(%s::interval, timestamp) AS bucket_time,
                interface_name,
                MAX(bytes_in) - MIN(bytes_in) AS bytes_in_diff,
                MAX(bytes_out) - MIN(bytes_out) AS bytes_out_diff,
                MAX(packets_in) - MIN(packets_in) AS packets_in_diff,
                MAX(packets_out) - MIN(packets_out) AS packets_out_diff,
                MAX(errors_in) - MIN(errors_in) AS errors_in_diff,
                MAX(errors_out) - MIN(errors_out) AS errors_out_diff,
                AVG(throughput_mbps) AS avg_throughput,
                MAX(throughput_mbps) AS max_throughput
            FROM snmp_monitoring_snmpinterfacestats
            WHERE {where_clause}
            GROUP BY bucket_time, interface_name
            ORDER BY bucket_time ASC, interface_name
        """
        
        params = [interval] + params
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'bucket_time': row[0],
                    'interface_name': row[1],
                    'bytes_in_diff': int(row[2]) if row[2] is not None else 0,
                    'bytes_out_diff': int(row[3]) if row[3] is not None else 0,
                    'packets_in_diff': int(row[4]) if row[4] is not None else 0,
                    'packets_out_diff': int(row[5]) if row[5] is not None else 0,
                    'errors_in_diff': int(row[6]) if row[6] is not None else 0,
                    'errors_out_diff': int(row[7]) if row[7] is not None else 0,
                    'avg_throughput': float(row[8]) if row[8] is not None else None,
                    'max_throughput': float(row[9]) if row[9] is not None else None,
                })
            
            return Response({
                'aggregated_data': results,
                'interval': interval,
                'count': len(results),
                'metadata': {
                    'device_id': int(device_id),
                    'interface_name': interface_name,
                }
            })
            
        except Exception as e:
            logger.exception("Error in SNMP interface stats aggregation")
            return Response(
                {"error": f"Database error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='interfaces')
    def interfaces(self, request):
        """
        Get list of unique interfaces for a device.
        
        Query Parameters:
        - device_id (required): SNMP device ID
        
        Returns:
        {
            "interfaces": ["eth0", "eth1", "wlan0"],
            "count": 3
        }
        """
        device_id = request.query_params.get('device_id')
        if not device_id:
            return Response(
                {"error": "device_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        interfaces = SNMPInterfaceStats.objects.filter(
            device_id=device_id
        ).values_list('interface_name', flat=True).distinct().order_by('interface_name')
        
        return Response({
            'interfaces': list(interfaces),
            'count': len(interfaces)
        })

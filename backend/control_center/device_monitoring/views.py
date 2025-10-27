# File: views.py
# Copyright (C) 2025 Taurine Technology
#
# This file is part of the SDN Launch Control project.
#
# This project is licensed under the GNU General Public License v3.0 (GPL-3.0),
# available at: https://www.gnu.org/licenses/gpl-3.0.en.html#license-text
#
# Contributions to this project are governed by a Contributor License Agreement (CLA).
# By submitting a contribution, contributors grant Taurine Technology exclusive rights to
# the contribution, including the right to relicense it under a different license
# at the copyright owner's discretion.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the GNU General Public License for more details.
#
# For inquiries, contact Keegan White at keeganwhite@taurinetech.com.

import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from general.models import Device, Bridge, Port
from django.shortcuts import get_object_or_404
import json
import os
from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .models import DeviceStats, PortUtilizationStats
from .serializers import PortUtilizationStatsSerializer
from network_device.models import NetworkDevice
from network_device.serializers import NetworkDeviceSerializer
from requests.auth import HTTPBasicAuth
from rest_framework.decorators import api_view, authentication_classes
from ovs_install.utilities.ansible_tasks import run_playbook
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError
import logging
from onos.models import OnosOpenFlowDevice
from ovs_install.utilities.utils import (write_to_inventory, save_ip_to_config, save_bridge_name_to_config,
    save_interfaces_to_config, save_openflow_version_to_config, save_controller_port_to_config,
    save_controller_ip_to_config, save_api_url_to_config, save_api_url_to_config, save_port_to_clients, save_switch_id,
                                         save_api_base_url, save_port_to_router, save_model_name, save_num_bytes,
                                         save_num_packets, save_monitor_interface)
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from django.db import connection
from django.utils.dateparse import parse_datetime
from django.utils import timezone
import re
from datetime import datetime, timedelta
import pytz
from utils.ansible_utils import run_playbook_with_extravars, create_temp_inv, create_inv_data

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
logger = logging.getLogger(__name__)
install_system_monitor = "install-stats-monitor"
install_qos_monitor = "run-ovs-qos-monitor"
playbook_dir_path = f"{parent_dir}/ansible/playbooks"
inventory_path = f"{parent_dir}/ansible/inventory/inventory"
config_path = f"{parent_dir}/ansible/group_vars/all.yml"


@api_view(['POST'])
def install_system_stats_monitor(request):
    try:
        data = request.data
        validate_ipv4_address(data.get('lan_ip_address'))
        lan_ip_address = data.get('lan_ip_address')
        write_to_inventory(lan_ip_address, data.get('username'), data.get('password'), inventory_path)
        save_ip_to_config(lan_ip_address, config_path)
        save_api_url_to_config(data.get('api_url'), config_path)
        result_install = run_playbook(install_system_monitor, playbook_dir_path, inventory_path)
        return Response({"status": "success", "message": 'system monitor installed'}, status=status.HTTP_200_OK)
    except ValidationError:
        return Response({"status": "error", "message": "Invalid IP address format."},
                        status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(e)
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def install_ovs_qos_monitor(request):
    try:
        data = request.data
        # print('***')
        # print(data)
        # print('***')
        validate_ipv4_address(data.get('lan_ip_address'))
        lan_ip_address = data.get('lan_ip_address')
        bridge_name = data.get('name')
        openflow_version = data.get('openflow_version')
        device = get_object_or_404(Device, lan_ip_address=lan_ip_address, device_type='switch')
        api_url = data.get('api_url')

        inv_content = create_inv_data(lan_ip_address, device.username, device.password)
        inv_path = create_temp_inv(inv_content)

        result_install = run_playbook_with_extravars(
            install_qos_monitor,
            playbook_dir_path,
            inv_path,
            {
                'ip_address': lan_ip_address,
                'bridge_name': bridge_name,
                'openflow_version': 'openflow13',
                'api_url': api_url
            },
            quiet=False
        )

        # save_openflow_version_to_config(openflow_version, config_path)
        # save_bridge_name_to_config(bridge_name, config_path)
        # device = get_object_or_404(Device, lan_ip_address=lan_ip_address)
        # write_to_inventory(lan_ip_address, device.username, device.password, inventory_path)
        # save_ip_to_config(lan_ip_address, config_path)
        # save_api_url_to_config(data.get('api_url'), config_path)
        # result_install = run_playbook(install_qos_monitor, playbook_dir_path, inventory_path)
        # print(result_install)
        return Response({"status": "success", "message": 'QoS monitor installed'}, status=status.HTTP_200_OK)
    except ValidationError:
        return Response({"status": "error", "message": "Invalid IP address format."},
                        status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(e)
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
def post_device_stats(request):
    try:
        # Parse the JSON data from the request
        data = json.loads(request.body)
        
        # Validate required fields
        ip_address = data.get('ip_address')
        if not ip_address:
            logger.warning("Received device stats without ip_address")
            return Response({"status": "error", "message": "ip_address is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Persist stats to database
        try:
            DeviceStats.objects.create(
                ip_address=ip_address,
                cpu=data.get('cpu', 0.0),
                memory=data.get('memory', 0.0),
                disk=data.get('disk', 0.0)
            )
        except Exception:
            logger.exception("Failed to save device stats to database")
        
        # Get the channel layer and send the data to the 'device_stats' group
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'device_stats',
            {
                'type': 'device.message',
                'device': data
            }
        )
        return Response({"status": "success"}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("Error in post_device_stats")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
def post_openflow_metrics(request):
    """
    Receives OpenFlow port metrics from qos.py script and stores port utilization stats.
    
    Expected data format from qos.py:
    {
        "device_ip": "10.10.10.5",
        "stats": {
            "port_name": {
                "rx_bytes_diff": int,
                "tx_bytes_diff": int, 
                "duration_diff": float
            }
        }
    }
    """
    try:
        data = json.loads(request.body)
        device_ip = data['device_ip']
        stats = data['stats']
        throughput_data = {
            'ip_address': device_ip,
            'ports': {}
        }

        for port_name, values in stats.items():
            # Calculate throughput in bytes per second
            if values['duration_diff'] > 0:
                throughput_bps = (values['rx_bytes_diff'] * 8) / values['duration_diff']
                throughput_mbps = throughput_bps / 1000000
            else:
                throughput_mbps = 0
            throughput_data['ports'][port_name] = throughput_mbps

            # Store port utilization stats in database
            try:
                # Query Port model to get link_speed for utilization calculation
                port_obj = Port.objects.filter(
                    device__lan_ip_address=device_ip, 
                    name=port_name
                ).first()
                
                link_speed_mbps = None
                utilization_percent = None
                
                if port_obj and port_obj.link_speed:
                    link_speed_mbps = port_obj.link_speed
                    if throughput_mbps > 0 and link_speed_mbps > 0:
                        utilization_percent = (throughput_mbps / link_speed_mbps) * 100
                    else:
                        utilization_percent = 0.0
                else:
                    # No link_speed configured, set utilization to 0 but store throughput
                    utilization_percent = 0.0
                    # logger.warning(f"No link_speed configured for port {port_name} on device {device_ip}")

                # Create PortUtilizationStats record
                PortUtilizationStats.objects.create(
                    ip_address=device_ip,
                    port_name=port_name,
                    throughput_mbps=throughput_mbps,
                    utilization_percent=utilization_percent,
                    rx_bytes_diff=values['rx_bytes_diff'],
                    tx_bytes_diff=values['tx_bytes_diff'],
                    duration_diff=values['duration_diff']
                )
                
            except Exception as db_e:
                # Log database errors but don't fail the request
                logger.exception(f"Failed to store port utilization stats for {port_name} on {device_ip}: {db_e}")

        # Continue with existing WebSocket functionality
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "openflow_metrics",
            {
                "type": "openflow_message",
                "message": throughput_data
            }
        )
        return Response({"status": "success"}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("Error in post_openflow_metrics")
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def install_sniffer(request):
    try:
        data = request.data
        # device to install on
        lan_ip_address = data.get('lan_ip_address')
        validate_ipv4_address(lan_ip_address)
        device = get_object_or_404(Device, lan_ip_address=lan_ip_address)


        save_switch_id('0', config_path)
        api_base_url = data['api_base_url']
        monitor_interface = data['monitor_interface']
        port_to_client = data['port_to_client']
        port_to_router = data['port_to_router']
        save_num_packets(5, config_path)
        save_num_bytes(225, config_path)

        # save config
        write_to_inventory(lan_ip_address, device.username, device.password, inventory_path)
        save_ip_to_config(lan_ip_address, config_path)

        save_api_base_url(api_base_url, config_path)
        save_monitor_interface(monitor_interface, config_path)
        save_port_to_clients(port_to_client, config_path)
        save_port_to_router(port_to_router, config_path)
        save_model_name('testing_sniffer', config_path)

        result = run_playbook('install-sniffer', playbook_dir_path, inventory_path)

        return Response({"status": "success", "message": 'successfully installed sniffer'}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PortUtilizationStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for querying port utilization statistics optimized for time-series graphing.
    
    Query Parameters:
    - ip_address (required): Device IP to filter by (e.g., "10.10.10.5")
    - port_name (optional): Specific port name (e.g., "eth0", "enxf0a731a0f537")
    - start_time (recommended): ISO 8601 format (e.g., "2025-10-15T00:00:00Z")
    - end_time (optional): ISO 8601 format (default: now)
    - limit (optional): Max records to return (default: 10000, max: 50000)
    - hours (optional): Shortcut for last N hours (e.g., hours=24)
    - days (optional): Shortcut for last N days (e.g., days=7)
    
    Examples:
    - Last 24 hours for device: ?ip_address=10.10.10.5&hours=24
    - Specific port, last week: ?ip_address=10.10.10.5&port_name=eth0&days=7
    - Custom range: ?ip_address=10.10.10.5&start_time=2025-10-15T00:00:00Z&end_time=2025-10-20T00:00:00Z
    
    For aggregated data (recommended for graphs), use the /aggregate/ endpoint.
    """
    serializer_class = PortUtilizationStatsSerializer
    permission_classes = [IsAuthenticated]
    
    # Safety limit to prevent excessive data returns
    MAX_LIMIT = 50000
    DEFAULT_LIMIT = 10000

    def list(self, request, *args, **kwargs):
        """
        Override list to add warnings and metadata for UI consumption.
        """
        # Require ip_address filter for safety
        if not request.query_params.get('ip_address'):
            return Response(
                {
                    "error": "ip_address parameter is required",
                    "hint": "Use ?ip_address=10.10.10.5 to filter by device",
                    "recommendation": "For graphing, use the /aggregate/ endpoint for better performance"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.filter_queryset(self.get_queryset())
        
        # Get count before limiting
        total_count = queryset.count()
        
        # Apply limit
        limit = self._get_limit()
        queryset = queryset[:limit]
        
        serializer = self.get_serializer(queryset, many=True)
        
        # Return with metadata
        response_data = serializer.data
        
        # Add warning if results were limited
        metadata = {
            'count': len(response_data),
            'total_available': total_count,
            'limit_applied': limit,
        }
        
        if total_count > limit:
            metadata['warning'] = f"Results limited to {limit} records. {total_count - limit} records not returned."
            metadata['recommendation'] = "Use start_time/end_time filters or the /aggregate/ endpoint for better performance."
        
        return Response({
            'data': response_data,
            'metadata': metadata
        })

    def _get_limit(self):
        """Get and validate the limit parameter."""
        limit_param = self.request.query_params.get('limit')
        if limit_param:
            try:
                limit = int(limit_param)
                return min(limit, self.MAX_LIMIT)
            except ValueError:
                return self.DEFAULT_LIMIT
        return self.DEFAULT_LIMIT

    def get_queryset(self):
        """
        Filter queryset based on query parameters optimized for time-series data.
        """
        queryset = PortUtilizationStats.objects.all()
        
        # IP address filter (REQUIRED for safety)
        ip_address = self.request.query_params.get('ip_address')
        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)
        
        # Port name filter (optional - useful for specific interface graphs)
        port_name = self.request.query_params.get('port_name')
        if port_name:
            queryset = queryset.filter(port_name=port_name)
        
        # Time range filters
        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')
        
        # Convenient shortcuts for common time periods
        hours = self.request.query_params.get('hours')
        days = self.request.query_params.get('days')
        
        if hours:
            try:
                hours_float = float(hours)
                start_time = (timezone.now() - timezone.timedelta(hours=hours_float)).isoformat()
            except ValueError:
                logger.warning(f"Invalid hours parameter: {hours}")
        
        if days:
            try:
                days_int = int(days)
                start_time = (timezone.now() - timezone.timedelta(days=days_int)).isoformat()
            except ValueError:
                logger.warning(f"Invalid days parameter: {days}")
        
        # Apply start_time filter
        if start_time:
            try:
                start_dt = parse_datetime(start_time)
                if start_dt:
                    queryset = queryset.filter(timestamp__gte=start_dt)
            except ValueError:
                logger.warning(f"Invalid start_time format: {start_time}")
        
        # Apply end_time filter
        if end_time:
            try:
                end_dt = parse_datetime(end_time)
                if end_dt:
                    queryset = queryset.filter(timestamp__lte=end_dt)
            except ValueError:
                logger.warning(f"Invalid end_time format: {end_time}")
        
        # Order by timestamp ascending (oldest first) for proper graph rendering
        return queryset.order_by('timestamp')

    @action(detail=False, methods=['get'], url_path='aggregate')
    def aggregate(self, request):
        """
        Aggregate port utilization data using TimescaleDB time_bucket function.
        
        Returns time-bucketed data for time-series charts.
        Supports both single-device and network-wide queries.
        
        Query Parameters:
        - ip_address (optional): Device IP to filter by. If omitted, returns ALL devices.
        - port_name (optional): Specific port name
        - start_time (recommended): ISO 8601 format
        - end_time (optional): ISO 8601 format (default: now)
        - interval (optional): Time bucket size (default: '10 seconds' for spike detection)
          Valid: '1 second', '10 seconds', '30 seconds', '1 minute', '5 minutes', 
                 '15 minutes', '1 hour', '1 day'
          Use 'none' or 'raw' to get unbucketed raw data points
        - hours (optional): Shortcut for last N hours
        - days (optional): Shortcut for last N days
        
        Examples:
        - All devices, catch spikes: ?hours=1&interval=10 seconds
        - All devices, raw data: ?hours=0.1&interval=raw
        - Single device, 5min buckets: ?ip_address=10.10.10.5&hours=24&interval=5 minutes
        - Network-wide, 1min buckets: ?hours=6&interval=1 minute
        
        Returns: Time-series data perfect for line graphs (ordered oldest to newest).
        Network spikes are captured with 10-second default granularity.
        """
        # ip_address is now OPTIONAL - can query entire network
        ip_address = request.query_params.get('ip_address')
        
        # Get filter parameters
        port_name = request.query_params.get('port_name')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        interval = request.query_params.get('interval', '10 seconds')  # Default to 10s for spike detection
        
        # Handle convenient time shortcuts
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
        
        # Check if raw/unbucketed data requested
        use_raw_data = interval.lower() in ['none', 'raw', 'unbucketed']
        
        # Validate interval parameter (unless raw data requested)
        if not use_raw_data:
            valid_intervals = [
                '1 second', '10 seconds', '30 seconds',
                '1 minute', '5 minutes', '15 minutes', 
                '1 hour', '1 day'
            ]
            if interval not in valid_intervals:
                return Response(
                    {"error": f"Invalid interval. Must be one of: {valid_intervals} or 'raw'"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Build SQL query for TimescaleDB aggregation with parameter binding
        where_conditions = []
        params = []
        
        # Add interval parameter only if bucketing is enabled
        if not use_raw_data:
            params = [interval]  # First parameter is the interval
        
        # ip_address is now optional - allows network-wide queries
        if ip_address:
            where_conditions.append("ip_address = %s")
            params.append(ip_address)
        
        if port_name:
            where_conditions.append("port_name = %s")
            params.append(port_name)
        
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
        
        # Construct the TimescaleDB query
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        if use_raw_data:
            # Raw unbucketed data - return individual data points
            query = f"""
                SELECT 
                    timestamp AS bucket_time,
                    ip_address,
                    port_name,
                    utilization_percent as avg_utilization,
                    utilization_percent as max_utilization,
                    throughput_mbps as avg_throughput,
                    throughput_mbps as max_throughput
                FROM device_monitoring_portutilizationstats
                WHERE {where_clause}
                ORDER BY timestamp ASC, ip_address, port_name
            """
        else:
            # Time-bucketed aggregated data
            query = f"""
                SELECT 
                    time_bucket(%s::interval, timestamp) AS bucket_time,
                    ip_address,
                    port_name,
                    AVG(utilization_percent) as avg_utilization,
                    MAX(utilization_percent) as max_utilization,
                    AVG(throughput_mbps) as avg_throughput,
                    MAX(throughput_mbps) as max_throughput
                FROM device_monitoring_portutilizationstats
                WHERE {where_clause}
                GROUP BY bucket_time, ip_address, port_name
                ORDER BY bucket_time ASC, ip_address, port_name
            """

        logger.info(f"Query type: {'raw' if use_raw_data else 'bucketed'}")
        logger.info(f"Params: {params}")
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
            
            # Format results
            results = []
            for row in rows:
                results.append({
                    'bucket_time': row[0],
                    'ip_address': row[1], 
                    'port_name': row[2],
                    'avg_utilization': float(row[3]) if row[3] is not None else None,
                    'max_utilization': float(row[4]) if row[4] is not None else None,
                    'avg_throughput': float(row[5]) if row[5] is not None else None,
                    'max_throughput': float(row[6]) if row[6] is not None else None,
                })
            
            return Response({
                'aggregated_data': results,
                'interval': 'raw (unbucketed)' if use_raw_data else interval,
                'count': len(results),
                'bucketed': not use_raw_data
            })
            
        except Exception as e:
            logger.exception("Error in port utilization aggregation")
            return Response(
                {"error": f"Database error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='all-devices')
    def all_devices(self, request):
        """
        Get ALL devices with ALL their active ports in one request.
        
        Returns complete network overview.
        Only includes ports that have actual data (filters out inactive/unused ports).
        
        Query Parameters:
        - start_time (recommended): ISO 8601 format
        - end_time (optional): ISO 8601 format (default: now)
        - interval (optional): Time bucket size (default: '5 minutes')
        - hours (optional): Shortcut for last N hours
        - days (optional): Shortcut for last N days
        - min_utilization (optional): Filter ports with avg utilization >= this value (default: 0)
        
        Returns: All devices grouped with their active ports and summary statistics.
        
        Example Response:
        {
          "devices": {
            "10.10.10.5": {
              "ip_address": "10.10.10.5",
              "total_ports": 3,
              "active_ports": 2,
              "busiest_port": "eth0",
              "total_throughput": 220.5,
              "avg_utilization": 38.5,
              "ports": {
                "eth0": {
                  "current": { "utilization": 45.2, "throughput": 125.5 },
                  "average": { "utilization": 42.1, "throughput": 118.3 },
                  "peak": { "utilization": 78.5, "throughput": 250.0 }
                },
                "eth1": { ... }
              }
            },
            "10.10.10.6": { ... }
          },
          "summary": {
            "total_devices": 2,
            "total_ports": 6,
            "busiest_device": "10.10.10.5",
            "total_network_throughput": 450.8
          }
        }
        """
        # Get time parameters
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        interval = request.query_params.get('interval', '5 minutes')
        hours = request.query_params.get('hours')
        days = request.query_params.get('days')
        min_utilization = request.query_params.get('min_utilization', 0)
        
        try:
            min_utilization = float(min_utilization)
        except ValueError:
            min_utilization = 0
        
        # Handle time shortcuts
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
        
        # Default to last 24 hours
        if not start_time and not hours and not days:
            start_time = (timezone.now() - timezone.timedelta(hours=24)).isoformat()
        
        # Validate interval
        valid_intervals = ['1 minute', '5 minutes', '15 minutes', '1 hour', '1 day']
        if interval not in valid_intervals:
            return Response(
                {"error": f"Invalid interval. Must be one of: {valid_intervals}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build query - get all devices with data
        where_conditions = []
        params = []
        
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
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = f"""
            SELECT 
                ip_address,
                port_name,
                AVG(utilization_percent) as avg_utilization,
                MAX(utilization_percent) as max_utilization,
                AVG(throughput_mbps) as avg_throughput,
                MAX(throughput_mbps) as max_throughput,
                COUNT(*) as data_point_count
            FROM device_monitoring_portutilizationstats
            WHERE {where_clause}
            GROUP BY ip_address, port_name
            HAVING AVG(utilization_percent) >= %s OR AVG(throughput_mbps) > 0
            ORDER BY ip_address, port_name
        """
        
        params.append(min_utilization)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
            
            # Group by device, then by port
            devices = {}
            
            for row in rows:
                ip_address = row[0]
                port_name = row[1]
                avg_util = float(row[2]) if row[2] is not None else 0
                max_util = float(row[3]) if row[3] is not None else 0
                avg_throughput = float(row[4]) if row[4] is not None else 0
                max_throughput = float(row[5]) if row[5] is not None else 0
                data_points = int(row[6]) if row[6] is not None else 0
                
                # Initialize device if not exists
                if ip_address not in devices:
                    devices[ip_address] = {
                        'ip_address': ip_address,
                        'ports': {},
                        'total_utilization': 0,
                        'total_throughput': 0,
                        'max_utilization': 0,
                        'busiest_port': None,
                        'port_count': 0
                    }
                
                # Add port data
                devices[ip_address]['ports'][port_name] = {
                    'port_name': port_name,
                    'average': {
                        'utilization': round(avg_util, 2),
                        'throughput': round(avg_throughput, 2)
                    },
                    'peak': {
                        'utilization': round(max_util, 2),
                        'throughput': round(max_throughput, 2)
                    },
                    'data_points': data_points
                }
                
                # Accumulate device stats
                devices[ip_address]['total_utilization'] += avg_util
                devices[ip_address]['total_throughput'] += avg_throughput
                devices[ip_address]['port_count'] += 1
                
                # Track busiest port
                if avg_util > devices[ip_address]['max_utilization']:
                    devices[ip_address]['max_utilization'] = avg_util
                    devices[ip_address]['busiest_port'] = port_name
            
            # Format device responses
            formatted_devices = {}
            total_network_throughput = 0
            busiest_device = None
            max_device_util = 0
            
            for ip_address, device_data in devices.items():
                port_count = device_data['port_count']
                avg_device_utilization = device_data['total_utilization'] / port_count if port_count > 0 else 0
                
                formatted_devices[ip_address] = {
                    'ip_address': ip_address,
                    'total_ports': port_count,
                    'active_ports': len([p for p in device_data['ports'].values() if p['average']['throughput'] > 0]),
                    'busiest_port': device_data['busiest_port'],
                    'total_throughput': round(device_data['total_throughput'], 2),
                    'avg_utilization': round(avg_device_utilization, 2),
                    'ports': device_data['ports']
                }
                
                # Track for summary
                total_network_throughput += device_data['total_throughput']
                if avg_device_utilization > max_device_util:
                    max_device_util = avg_device_utilization
                    busiest_device = ip_address
            
            # Build response
            response_data = {
                'devices': formatted_devices,
                'time_range': {
                    'start': start_time,
                    'end': end_time or timezone.now().isoformat()
                },
                'interval': interval,
                'summary': {
                    'total_devices': len(devices),
                    'total_ports': sum(d['total_ports'] for d in formatted_devices.values()),
                    'total_active_ports': sum(d['active_ports'] for d in formatted_devices.values()),
                    'busiest_device': busiest_device,
                    'total_network_throughput': round(total_network_throughput, 2),
                    'timestamp': timezone.now().isoformat()
                }
            }
            
            return Response(response_data)
            
        except Exception as e:
            logger.exception("Error in all-devices aggregation")
            return Response(
                {"error": f"Database error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# toggle_device_monitoring function removed - use NetworkDeviceViewSet instead
# Example usage:
# PATCH /api/v1/network-devices/{device_id}/
# {"is_ping_target": true}


class DeviceUptimeViewSet(viewsets.ViewSet):
    """
    Unified ViewSet for device uptime data with multiple aggregation methods.
    
    This replaces the individual function-based views with a more maintainable
    approach using Django REST Framework's built-in capabilities.
    
    Endpoints:
    - GET /api/device-monitoring/uptime/ - List uptime status for all devices
    - GET /api/device-monitoring/uptime/{device_id}/timeseries/ - Time series data for specific device
    - GET /api/device-monitoring/uptime/aggregates/ - Aggregated data from materialized views
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """
        Returns current uptime percentage for monitored devices over a time period.
        
        Query Parameters:
            - period: Look-back time period (default: '15 minutes')
            - min_pings: Minimum number of pings required (default: 1)
            - device_ids: Comma-separated list of device IDs to filter
        """
        return self._get_uptime_status(request)
    
    @action(detail=True, methods=['get'], url_path='timeseries')
    def timeseries(self, request, pk=None):
        """
        Returns time-bucketed uptime data for a specific device.
        
        Query Parameters:
            - period: Look-back time period (default: '30 minutes')
            - bucket_interval: Time bucket size (default: '5 minutes')
        """
        return self._get_device_timeseries(request, pk)
    
    @action(detail=False, methods=['get'], url_path='aggregates')
    def aggregates(self, request):
        """
        Returns aggregated ping data from materialized views.
        
        Query Parameters:
            - device_ids: Comma-separated list of device IDs
            - aggregation: One of "15m", "60m", "6h", "12h", "24h", "7d", "30d", "90d", "365d"
            - time_range: Time range filter (default: "24 hours")
        """
        return self._get_ping_aggregates(request)
    
    def _get_uptime_status(self, request):
        """Consolidated uptime status logic."""
        period = request.query_params.get('period', '15 minutes')
        min_pings = int(request.query_params.get('min_pings', 1))
        device_ids_param = request.query_params.get('device_ids')
        
        # Parse device_ids
        device_ids = self._parse_device_ids(device_ids_param)
        if isinstance(device_ids, Response):
            return device_ids
        
        # Build SQL query
        sql, params = self._build_uptime_query(period, device_ids, min_pings)
        
        # Execute query
        results = self._execute_query(sql, params)
        if isinstance(results, Response):
            return results
        
        # Process results
        return self._process_uptime_results(results, period, device_ids)
    
    def _get_device_timeseries(self, request, device_id):
        """Consolidated timeseries logic."""
        period = request.query_params.get('period', '30 minutes')
        bucket_interval = request.query_params.get('bucket_interval', '5 minutes')
        valid_intervals = ['1 minute', '5 minutes', '15 minutes', '1 hour', '1 day']
        if bucket_interval not in valid_intervals:
            return Response(
                {"error": f"Invalid bucket_interval. Must be one of: {valid_intervals}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate device exists
        if not NetworkDevice.objects.filter(id=device_id).exists():
            return Response(
                {"error": f"Device with id {device_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate period
        period_minutes = parse_period_to_minutes(period)
        if period_minutes < 30:
            return Response(
                {"error": "Minimum period is 30 minutes"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        # Build optimized TimescaleDB query with advanced features
        sql = """
            SELECT
                time_bucket(%s::interval, timestamp) AS bucket,
                AVG(CASE WHEN is_alive THEN 1.0 ELSE 0 END) * 100 AS uptime_percentage,
                COUNT(*) AS total_pings,
                MIN(CASE WHEN is_alive THEN timestamp END) AS first_alive,
                MAX(CASE WHEN is_alive THEN timestamp END) AS last_alive,
                COUNT(CASE WHEN is_alive THEN 1 END) AS alive_count
            FROM device_monitoring_devicepingstats
            WHERE device_id = %s 
              AND timestamp >= now() - interval %s
            GROUP BY bucket
            ORDER BY bucket;
        """
        params = [bucket_interval, device_id, period]
        
        results = self._execute_query(sql, params)
        if isinstance(results, Response):
            return results
        
        # Fill missing buckets
        return self._fill_time_buckets(results, period_minutes, bucket_interval)
    
    def _get_ping_aggregates(self, request):
        """Consolidated ping aggregates logic with fallback to direct queries."""
        device_ids_param = request.query_params.get('device_ids')
        aggregation_param = request.query_params.get('aggregation', '15m')
        time_range = request.query_params.get('time_range', '24 hours')
        
        # Parse device_ids
        device_ids = self._parse_device_ids(device_ids_param)
        if isinstance(device_ids, Response):
            return device_ids
        
        # Map aggregation to time intervals for direct queries
        aggregation_intervals = {
            '15m': '15 minutes',
            '60m': '1 hour', 
            '6h': '6 hours',
            '12h': '12 hours',
            '24h': '24 hours',
            '7d': '7 days',
            '30d': '30 days',
            '90d': '90 days',
            '365d': '365 days',
        }
        
        if aggregation_param not in aggregation_intervals:
            return Response(
                {"error": f"Invalid aggregation value. Allowed values are: {', '.join(aggregation_intervals.keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use direct TimescaleDB query instead of materialized views
        bucket_interval = aggregation_intervals[aggregation_param]
        
        # Build direct query using time_bucket
        sql = """
            SELECT 
                time_bucket(%s::interval, timestamp) AS bucket,
                device_id,
                AVG(CASE WHEN is_alive THEN 1.0 ELSE 0 END) * 100 AS uptime_percentage,
                COUNT(*) AS total_pings
            FROM device_monitoring_devicepingstats
            WHERE timestamp >= now() - interval %s
        """
        params = [bucket_interval, time_range]
        
        if device_ids:
            placeholders = ','.join(['%s'] * len(device_ids))
            sql += f" AND device_id IN ({placeholders})"
            params.extend(device_ids)
        
        sql += """
            GROUP BY bucket, device_id
            ORDER BY bucket DESC, device_id;
        """
        
        # Execute query
        results = self._execute_query(sql, params)
        if isinstance(results, Response):
            return results
        
        return Response(results, status=status.HTTP_200_OK)
    
    def _parse_device_ids(self, device_ids_param):
        """Parse comma-separated device IDs."""
        if not device_ids_param:
            return []
        
        try:
            return [int(x.strip()) for x in device_ids_param.split(',') if x.strip()]
        except ValueError:
            return Response(
                {"error": "device_ids must be a comma-separated list of integers."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _build_uptime_query(self, period, device_ids, min_pings):
        """Build optimized TimescaleDB query for uptime status."""
        # Use TimescaleDB's time_bucket for efficient aggregation
        # Leverage compression and chunk exclusion for fast lookups
        sql = """
            SELECT
                device_id,
                AVG(CASE WHEN is_alive THEN 1.0 ELSE 0 END) * 100 AS uptime_percentage,
                COUNT(*) AS total_pings,
                MIN(timestamp) AS first_ping,
                MAX(timestamp) AS last_ping
            FROM device_monitoring_devicepingstats
            WHERE timestamp >= now() - interval %s
        """
        params = [period]
        
        if device_ids:
            placeholders = ','.join(['%s'] * len(device_ids))
            sql += f" AND device_id IN ({placeholders})"
            params.extend(device_ids)
        
        sql += """
            GROUP BY device_id
            HAVING COUNT(*) >= %s
            ORDER BY device_id;
        """
        params.append(min_pings)
        
        return sql, params
    
# _build_aggregates_query method removed - using direct TimescaleDB queries instead
    
    def _execute_query(self, sql, params):
        """Execute TimescaleDB query."""
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.exception("Error executing uptime query")
            return Response(
                {"error": f"Database query error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _process_uptime_results(self, results, period, device_ids):
        """Process uptime results with missing device handling and enrichment."""
        # Add missing devices as offline
        if device_ids:
            all_device_ids = set(device_ids)
        else:
            all_device_ids = set(
                NetworkDevice.objects.filter(is_ping_target=True)
                .values_list('id', flat=True)
            )
        
        result_device_ids = set(r['device_id'] for r in results)
        missing_device_ids = all_device_ids - result_device_ids
        
        for device_id in missing_device_ids:
            results.append({
                'device_id': device_id,
                'uptime_percentage': 0.0,
                'total_pings': 0
            })
        
        # Adjust for incomplete data
        period_minutes = parse_period_to_minutes(period)
        expected_pings = period_minutes
        
        for r in results:
            if r['total_pings'] < expected_pings:
                alive_pings = float(r['uptime_percentage']) * float(r['total_pings']) / 100.0
                r['uptime_percentage'] = (
                    (alive_pings / expected_pings) * 100 if expected_pings > 0 else 0.0
                )
                r['total_pings'] = expected_pings
        
        # Sort and enrich with device info
        results.sort(key=lambda r: r['device_id'])
        self._enrich_with_device_info(results)
        
        return Response(results, status=status.HTTP_200_OK)

    def _fill_time_buckets(self, results, period_minutes, bucket_interval):
        """Fill missing time buckets with 0% uptime."""
        now = datetime.utcnow().replace(second=0, microsecond=0, tzinfo=pytz.UTC)
        start_time = now - timedelta(minutes=period_minutes)
        
        bucket_minutes = parse_period_to_minutes(bucket_interval)
        bucket_delta = timedelta(minutes=bucket_minutes)
        
        # Generate expected buckets
        expected_buckets = []
        t = start_time.replace(second=0, microsecond=0)
        minutes_to_add = (bucket_minutes - t.minute % bucket_minutes) if t.minute % bucket_minutes != 0 else 0
        t = t + timedelta(minutes=minutes_to_add)
        
        while t <= now:
            expected_buckets.append(t)
            t += bucket_delta
        
        # Build result lookup
        result_by_bucket = {}
        for r in results:
            bucket_dt = r['bucket']
            if isinstance(bucket_dt, str):
                bucket_dt = datetime.fromisoformat(bucket_dt.replace('Z', '+00:00'))
            result_by_bucket[bucket_dt] = r
        
        # Fill missing buckets
        filled_results = []
        for bucket_time in expected_buckets:
            r = result_by_bucket.get(bucket_time)
            
            if r:
                bucket_val = r['bucket']
                if isinstance(bucket_val, datetime):
                    bucket_val = bucket_val.isoformat().replace('+00:00', 'Z')
                elif isinstance(bucket_val, str) and bucket_val.endswith('+00:00'):
                    bucket_val = bucket_val.replace('+00:00', 'Z')
                
                r = dict(r)
                r['bucket'] = bucket_val
                filled_results.append(r)
            else:
                filled_results.append({
                    'bucket': bucket_time.isoformat().replace('+00:00', 'Z'),
                    'uptime_percentage': 0.0,
                    'total_pings': 0
                })
        
        filled_results.sort(key=lambda r: r['bucket'])
        return Response(filled_results, status=status.HTTP_200_OK)

    def _enrich_with_device_info(self, results):
        """Enrich results with device information."""
        device_ids_in_results = [r['device_id'] for r in results]
        devices = NetworkDevice.objects.filter(id__in=device_ids_in_results).values(
            'id', 'name', 'is_ping_target', 'ip_address', 'mac_address'
        )
        device_lookup = {d['id']: d for d in devices}
        
        for r in results:
            device_info = device_lookup.get(r['device_id'], {})
            r['device_name'] = device_info.get('name') or f"Device {r['device_id']}"
            r['is_monitored'] = device_info.get('is_ping_target', False)
            r['ip_address'] = device_info.get('ip_address')
            r['mac_address'] = device_info.get('mac_address')


def parse_period_to_minutes(period):
    """
    Parse period strings like '15 minutes', '24 hours', '7 days' to minutes.
    
    Args:
        period (str): Time period string (e.g., "15 minutes", "2 hours", "7 days")
        
    Returns:
        int: Number of minutes
        
    Examples:
        >>> parse_period_to_minutes("15 minutes")
        15
        >>> parse_period_to_minutes("2 hours")
        120
        >>> parse_period_to_minutes("7 days")
        10080
    """
    period = period.strip().lower()
    
    # Try to match minutes
    match = re.match(r"(\d+)\s*minutes?", period)
    if match:
        return int(match.group(1))
    
    # Try to match hours
    match = re.match(r"(\d+)\s*hours?", period)
    if match:
        return int(match.group(1)) * 60
    
    # Try to match days
    match = re.match(r"(\d+)\s*days?", period)
    if match:
        return int(match.group(1)) * 60 * 24
    
    # Try to match weeks
    match = re.match(r"(\d+)\s*weeks?", period)
    if match:
        return int(match.group(1)) * 60 * 24 * 7
    
    # Default to 15 minutes if parsing fails
    logger.warning(f"Could not parse period '{period}', defaulting to 15 minutes")
    return 15


# aggregate_device_uptime_status function removed - use DeviceUptimeViewSet instead
# GET /api/device-monitoring/uptime/


# All old uptime functions removed - use DeviceUptimeViewSet instead
# GET /api/device-monitoring/uptime/ - List uptime status
# GET /api/device-monitoring/uptime/{device_id}/timeseries/ - Time series data
# GET /api/device-monitoring/uptime/aggregates/ - Materialized view aggregates

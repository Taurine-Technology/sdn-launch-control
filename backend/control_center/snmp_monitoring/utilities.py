# File: utilities.py
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
SNMP Utilities for polling network devices.

This module provides low-level SNMP communication functions and high-level
metric collection functions for monitoring network devices via SNMPv2c.
"""

import logging
import asyncio
from typing import Optional, List, Tuple, Dict, Any

# pysnmp 7.x uses the Slim API which is async-first
# We wrap it in asyncio.run() for synchronous usage
from pysnmp.hlapi.v1arch import (
    Slim,
    ObjectType,
    ObjectIdentity,
    Integer,
    Counter32,
    Counter64,
    Gauge32,
)

logger = logging.getLogger(__name__)

# ============================================================================
# OID Dictionary - Single source of truth for SNMP Object Identifiers
# ============================================================================

OIDS = {
    # Standard MIB-II (RFC 1213) - System group
    "system": {
        "sysDescr": "1.3.6.1.2.1.1.1.0",       # System description
        "sysObjectID": "1.3.6.1.2.1.1.2.0",    # System object ID
        "sysUpTime": "1.3.6.1.2.1.1.3.0",      # System uptime (in hundredths of seconds)
        "sysContact": "1.3.6.1.2.1.1.4.0",     # System contact
        "sysName": "1.3.6.1.2.1.1.5.0",        # System name
        "sysLocation": "1.3.6.1.2.1.1.6.0",    # System location
    },
    
    # Standard MIB-II - Interfaces group
    "interfaces": {
        "ifNumber": "1.3.6.1.2.1.2.1.0",              # Number of interfaces
        "ifIndex": "1.3.6.1.2.1.2.2.1.1",             # Interface index (table)
        "ifDescr": "1.3.6.1.2.1.2.2.1.2",             # Interface description (table)
        "ifType": "1.3.6.1.2.1.2.2.1.3",              # Interface type (table)
        "ifMtu": "1.3.6.1.2.1.2.2.1.4",               # Interface MTU (table)
        "ifSpeed": "1.3.6.1.2.1.2.2.1.5",             # Interface speed in bps (table)
        "ifPhysAddress": "1.3.6.1.2.1.2.2.1.6",       # Interface MAC address (table)
        "ifAdminStatus": "1.3.6.1.2.1.2.2.1.7",       # Admin status (table)
        "ifOperStatus": "1.3.6.1.2.1.2.2.1.8",        # Operational status (table)
        "ifInOctets": "1.3.6.1.2.1.2.2.1.10",         # Bytes in (table)
        "ifInUcastPkts": "1.3.6.1.2.1.2.2.1.11",      # Unicast packets in (table)
        "ifInDiscards": "1.3.6.1.2.1.2.2.1.13",       # Discarded inbound packets (table)
        "ifInErrors": "1.3.6.1.2.1.2.2.1.14",         # Inbound errors (table)
        "ifOutOctets": "1.3.6.1.2.1.2.2.1.16",        # Bytes out (table)
        "ifOutUcastPkts": "1.3.6.1.2.1.2.2.1.17",     # Unicast packets out (table)
        "ifOutDiscards": "1.3.6.1.2.1.2.2.1.19",      # Discarded outbound packets (table)
        "ifOutErrors": "1.3.6.1.2.1.2.2.1.20",        # Outbound errors (table)
    },
    
    # Vendor-specific OIDs
    "vendors": {
        "mikrotik": {
            # MikroTik-specific resource OIDs
            "mtxrHlCpuUsage": "1.3.6.1.4.1.14988.1.1.3.11.0",      # CPU usage percentage
            "mtxrHlTotalMemory": "1.3.6.1.4.1.14988.1.1.3.2.0",    # Total memory (bytes)
            "mtxrHlMemoryUsed": "1.3.6.1.4.1.14988.1.1.3.3.0",     # Used memory (bytes)
            "mtxrHlProcessorFrequency": "1.3.6.1.4.1.14988.1.1.3.9.0",  # CPU frequency
        },
        "ubiquiti": {
            # Ubiquiti EdgeOS uses standard host resources MIB
            # These are placeholders - will be refined based on actual device testing
            "hrProcessorLoad": "1.3.6.1.2.1.25.3.3.1.2.1",  # Host Resources CPU load
            "hrStorageUsed": "1.3.6.1.2.1.25.2.3.1.6",      # Host Resources storage used
            "hrStorageSize": "1.3.6.1.2.1.25.2.3.1.5",      # Host Resources storage size
        },
    },
}


# ============================================================================
# Low-Level SNMP Functions
# ============================================================================

def get_snmp_value(
    ip_address: str,
    community: str,
    oid: str,
    port: int = 161,
    timeout: int = 5
) -> Optional[str]:
    """
    Perform a single SNMP GET operation.
    
    Args:
        ip_address: Target device IP address
        community: SNMP community string (e.g., 'public')
        oid: SNMP Object Identifier to query
        port: SNMP port (default 161)
        timeout: Timeout in seconds (default 5)
    
    Returns:
        The SNMP value as a string, or None if error/timeout
    
    Example:
        >>> uptime = get_snmp_value('192.168.1.1', 'public', '1.3.6.1.2.1.1.3.0')
        >>> print(uptime)
        '123456789'
    """
    async def _async_get():
        """Async wrapper for SNMP GET using Slim API."""
        with Slim() as slim:
            error_indication, error_status, error_index, var_binds = await slim.get(
                community,
                ip_address,
                port,
                ObjectType(ObjectIdentity(oid)),
                timeout=timeout,
                retries=3
            )
            return error_indication, error_status, error_index, var_binds
    
    try:
        # Run the async function synchronously
        error_indication, error_status, error_index, var_binds = asyncio.run(_async_get())
        
        # Check for errors
        if error_indication:
            logger.warning(
                f"SNMP error for {ip_address} OID {oid}: {error_indication}"
            )
            return None
        elif error_status:
            logger.warning(
                f"SNMP error for {ip_address} OID {oid}: {error_status} "
                f"at {error_index and var_binds[int(error_index) - 1][0] or '?'}"
            )
            return None
        
        # Extract and return the value
        for var_bind in var_binds:
            # var_bind is a tuple of (ObjectIdentity, value)
            value = var_bind[1]
            return str(value)
        
        return None
        
    except Exception as e:
        logger.warning(f"Exception during SNMP GET to {ip_address} OID {oid}: {e}")
        return None


def walk_snmp_table(
    ip_address: str,
    community: str,
    base_oid: str,
    port: int = 161,
    timeout: int = 5
) -> List[Tuple[str, str]]:
    """
    Perform an SNMP WALK operation to retrieve a table.
    
    Args:
        ip_address: Target device IP address
        community: SNMP community string
        base_oid: Base OID to start walking from
        port: SNMP port (default 161)
        timeout: Timeout in seconds (default 5)
    
    Returns:
        List of (oid, value) tuples, or empty list on error
    
    Example:
        >>> interfaces = walk_snmp_table('192.168.1.1', 'public', '1.3.6.1.2.1.2.2.1.2')
        >>> for oid, name in interfaces:
        ...     print(f"{oid}: {name}")
    """
    async def _async_walk():
        """Async wrapper for SNMP WALK using Slim API."""
        results = []
        with Slim() as slim:
            async for (error_indication, error_status, error_index, var_binds) in slim.walk(
                community,
                ip_address,
                port,
                ObjectType(ObjectIdentity(base_oid)),
                timeout=timeout,
                retries=3
            ):
                # Check for errors
                if error_indication:
                    logger.warning(
                        f"SNMP walk error for {ip_address} OID {base_oid}: {error_indication}"
                    )
                    break
                elif error_status:
                    logger.warning(
                        f"SNMP walk error for {ip_address} OID {base_oid}: {error_status} at "
                        f"{error_index and var_binds[int(error_index) - 1][0] or '?'}"
                    )
                    break
                
                # Extract values
                for var_bind in var_binds:
                    oid = str(var_bind[0])
                    value = str(var_bind[1])
                    results.append((oid, value))
        
        return results
    
    try:
        # Run the async function synchronously
        return asyncio.run(_async_walk())
        
    except Exception as e:
        logger.warning(f"Exception during SNMP WALK to {ip_address} OID {base_oid}: {e}")
        return []


# ============================================================================
# High-Level Metric Collection Functions
# ============================================================================

def get_device_metrics(
    ip_address: str,
    community: str,
    vendor: str = "other",
    port: int = 161
) -> Optional[Dict[str, Any]]:
    """
    Collect general device metrics (CPU, memory, uptime) from an SNMP device.
    
    Args:
        ip_address: Target device IP address
        community: SNMP community string
        vendor: Device vendor (e.g., 'mikrotik', 'ubiquiti', 'other')
        port: SNMP port (default 161)
    
    Returns:
        Dictionary with metric keys:
            - cpu_usage: CPU usage percentage (float or None)
            - memory_usage: Memory usage percentage (float or None)
            - uptime_seconds: Uptime in seconds (int or None)
        Returns None if unable to collect any metrics.
    
    Example:
        >>> metrics = get_device_metrics('192.168.1.1', 'public', 'mikrotik')
        >>> print(metrics)
        {'cpu_usage': 12.5, 'memory_usage': 45.2, 'uptime_seconds': 86400}
    """
    metrics = {
        "cpu_usage": None,
        "memory_usage": None,
        "uptime_seconds": None,
    }
    
    # Always try to get uptime from standard MIB-II
    uptime_raw = get_snmp_value(ip_address, community, OIDS["system"]["sysUpTime"], port)
    if uptime_raw:
        try:
            # sysUpTime is in hundredths of seconds (TimeTicks)
            uptime_ticks = int(uptime_raw)
            metrics["uptime_seconds"] = uptime_ticks // 100
        except (ValueError, TypeError):
            logger.warning(f"Failed to parse uptime value for {ip_address}: {uptime_raw}")
    
    # Vendor-specific metrics
    if vendor.lower() == "mikrotik":
        # MikroTik CPU usage
        cpu_raw = get_snmp_value(
            ip_address, community, 
            OIDS["vendors"]["mikrotik"]["mtxrHlCpuUsage"], 
            port
        )
        if cpu_raw:
            try:
                metrics["cpu_usage"] = float(cpu_raw)
            except (ValueError, TypeError):
                logger.warning(f"Failed to parse MikroTik CPU value: {cpu_raw}")
        
        # MikroTik memory usage
        total_mem_raw = get_snmp_value(
            ip_address, community,
            OIDS["vendors"]["mikrotik"]["mtxrHlTotalMemory"],
            port
        )
        used_mem_raw = get_snmp_value(
            ip_address, community,
            OIDS["vendors"]["mikrotik"]["mtxrHlMemoryUsed"],
            port
        )
        
        if total_mem_raw and used_mem_raw:
            try:
                total_mem = float(total_mem_raw)
                used_mem = float(used_mem_raw)
                if total_mem > 0:
                    metrics["memory_usage"] = (used_mem / total_mem) * 100
            except (ValueError, TypeError, ZeroDivisionError) as e:
                logger.warning(f"Failed to calculate MikroTik memory usage: {e}")
    
    elif vendor.lower() == "ubiquiti":
        # Ubiquiti uses Host Resources MIB (placeholder - needs testing)
        # This is a simplified example; actual implementation may need table walks
        cpu_raw = get_snmp_value(
            ip_address, community,
            OIDS["vendors"]["ubiquiti"]["hrProcessorLoad"],
            port
        )
        if cpu_raw:
            try:
                metrics["cpu_usage"] = float(cpu_raw)
            except (ValueError, TypeError):
                logger.warning(f"Failed to parse Ubiquiti CPU value: {cpu_raw}")
    
    # Return None if we couldn't collect anything useful
    if all(v is None for v in metrics.values()):
        logger.warning(f"No metrics collected for {ip_address} (vendor: {vendor})")
        return None
    
    return metrics


def get_interface_statistics(
    ip_address: str,
    community: str,
    port: int = 161
) -> List[Dict[str, Any]]:
    """
    Collect interface-level statistics from an SNMP device.
    
    This function walks multiple SNMP interface tables and correlates data
    by interface index to build a comprehensive view of each interface.
    
    Args:
        ip_address: Target device IP address
        community: SNMP community string
        port: SNMP port (default 161)
    
    Returns:
        List of dictionaries, each containing:
            - interface_name: Interface description/name (str)
            - interface_index: SNMP interface index (int)
            - bytes_in: Total bytes received (int)
            - bytes_out: Total bytes transmitted (int)
            - packets_in: Total packets received (int)
            - packets_out: Total packets transmitted (int)
            - errors_in: Input errors (int)
            - errors_out: Output errors (int)
            - speed_bps: Interface speed in bits per second (int or None)
            - oper_status: Operational status (int or None, 1=up, 2=down)
    
    Example:
        >>> interfaces = get_interface_statistics('192.168.1.1', 'public')
        >>> for iface in interfaces:
        ...     print(f"{iface['interface_name']}: {iface['bytes_in']} bytes in")
    """
    # Walk all interface tables
    if_index_data = walk_snmp_table(ip_address, community, OIDS["interfaces"]["ifIndex"], port)
    if_descr_data = walk_snmp_table(ip_address, community, OIDS["interfaces"]["ifDescr"], port)
    if_speed_data = walk_snmp_table(ip_address, community, OIDS["interfaces"]["ifSpeed"], port)
    if_oper_status_data = walk_snmp_table(ip_address, community, OIDS["interfaces"]["ifOperStatus"], port)
    if_in_octets_data = walk_snmp_table(ip_address, community, OIDS["interfaces"]["ifInOctets"], port)
    if_out_octets_data = walk_snmp_table(ip_address, community, OIDS["interfaces"]["ifOutOctets"], port)
    if_in_pkts_data = walk_snmp_table(ip_address, community, OIDS["interfaces"]["ifInUcastPkts"], port)
    if_out_pkts_data = walk_snmp_table(ip_address, community, OIDS["interfaces"]["ifOutUcastPkts"], port)
    if_in_errors_data = walk_snmp_table(ip_address, community, OIDS["interfaces"]["ifInErrors"], port)
    if_out_errors_data = walk_snmp_table(ip_address, community, OIDS["interfaces"]["ifOutErrors"], port)
    
    # Build index-to-value mappings
    def build_index_map(data: List[Tuple[str, str]]) -> Dict[int, str]:
        """Extract interface index from OID and map to value."""
        index_map = {}
        for oid, value in data:
            # OID format: 1.3.6.1.2.1.2.2.1.X.INDEX where X is the column and INDEX is the interface index
            parts = oid.split('.')
            if len(parts) >= 2:
                try:
                    index = int(parts[-1])  # Last part is the interface index
                    index_map[index] = value
                except (ValueError, IndexError):
                    continue
        return index_map
    
    index_map = build_index_map(if_index_data)
    descr_map = build_index_map(if_descr_data)
    speed_map = build_index_map(if_speed_data)
    status_map = build_index_map(if_oper_status_data)
    in_octets_map = build_index_map(if_in_octets_data)
    out_octets_map = build_index_map(if_out_octets_data)
    in_pkts_map = build_index_map(if_in_pkts_data)
    out_pkts_map = build_index_map(if_out_pkts_data)
    in_errors_map = build_index_map(if_in_errors_data)
    out_errors_map = build_index_map(if_out_errors_data)
    
    # Build result list
    interfaces = []
    for if_index in sorted(index_map.keys()):
        try:
            interface = {
                "interface_name": descr_map.get(if_index, f"if{if_index}"),
                "interface_index": if_index,
                "bytes_in": int(in_octets_map.get(if_index, 0)),
                "bytes_out": int(out_octets_map.get(if_index, 0)),
                "packets_in": int(in_pkts_map.get(if_index, 0)),
                "packets_out": int(out_pkts_map.get(if_index, 0)),
                "errors_in": int(in_errors_map.get(if_index, 0)),
                "errors_out": int(out_errors_map.get(if_index, 0)),
                "speed_bps": int(speed_map[if_index]) if if_index in speed_map else None,
                "oper_status": int(status_map[if_index]) if if_index in status_map else None,
            }
            interfaces.append(interface)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse interface {if_index} data for {ip_address}: {e}")
            continue
    
    return interfaces


# ============================================================================
# Orchestrator Function - Ties SNMP helpers to Django models
# ============================================================================

def poll_snmp_device(device) -> Tuple[bool, Optional[str]]:
    """
    Main polling orchestrator that collects SNMP data and stores it in the database.
    
    This function:
    1. Reads device configuration from the SNMPDevice model
    2. Calls get_device_metrics() and get_interface_statistics()
    3. Stores results in SNMPMetrics and SNMPInterfaceStats models
    4. Updates device status (last_poll_attempt, last_successful_poll, consecutive_failures)
    
    Args:
        device: SNMPDevice model instance
    
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
        - (True, None) on success
        - (False, "error message") on failure
    
    Example:
        >>> from snmp_monitoring.models import SNMPDevice
        >>> device = SNMPDevice.objects.get(ip_address='192.168.1.1')
        >>> success, error = poll_snmp_device(device)
        >>> if success:
        ...     print("Polling successful!")
        ... else:
        ...     print(f"Polling failed: {error}")
    """
    from django.utils import timezone
    from .models import SNMPMetrics, SNMPInterfaceStats
    
    # Update last_poll_attempt immediately
    device.last_poll_attempt = timezone.now()
    
    try:
        # Collect device-level metrics
        logger.info(f"Polling SNMP device: {device.name} ({device.ip_address})")
        
        metrics = get_device_metrics(
            ip_address=device.ip_address,
            community=device.community_string,
            vendor=device.vendor,
            port=device.port
        )
        
        # If we got any metrics, store them
        if metrics:
            # Only create SNMPMetrics if we have at least one non-None value
            if any(v is not None for v in metrics.values()):
                SNMPMetrics.objects.create(
                    device=device,
                    cpu_usage=metrics.get('cpu_usage'),
                    memory_usage=metrics.get('memory_usage'),
                    uptime_seconds=metrics.get('uptime_seconds'),
                    # disk_usage is not collected yet, could be added later
                )
                logger.info(
                    f"Stored device metrics for {device.name}: "
                    f"CPU={metrics.get('cpu_usage')}%, "
                    f"MEM={metrics.get('memory_usage')}%, "
                    f"Uptime={metrics.get('uptime_seconds')}s"
                )
        else:
            logger.warning(f"No device metrics collected for {device.name}")
        
        # Collect interface statistics
        interfaces = get_interface_statistics(
            ip_address=device.ip_address,
            community=device.community_string,
            port=device.port
        )
        
        # Store interface statistics
        if interfaces:
            for iface in interfaces:
                SNMPInterfaceStats.objects.create(
                    device=device,
                    interface_name=iface['interface_name'],
                    interface_index=iface['interface_index'],
                    bytes_in=iface['bytes_in'],
                    bytes_out=iface['bytes_out'],
                    packets_in=iface['packets_in'],
                    packets_out=iface['packets_out'],
                    errors_in=iface['errors_in'],
                    errors_out=iface['errors_out'],
                    # throughput_mbps and utilization_percent could be calculated
                    # in a future enhancement by comparing with previous poll
                )
            logger.info(f"Stored statistics for {len(interfaces)} interfaces on {device.name}")
        else:
            logger.warning(f"No interface statistics collected for {device.name}")
        
        # Update device status on success
        device.last_successful_poll = timezone.now()
        device.consecutive_failures = 0
        device.save()
        
        return (True, None)
        
    except Exception as e:
        error_msg = f"Error polling {device.name} ({device.ip_address}): {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Update failure counter
        device.consecutive_failures += 1
        device.save()
        
        return (False, error_msg)


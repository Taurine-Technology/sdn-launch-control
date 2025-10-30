# File: utils.py
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

import subprocess
import logging
import tempfile
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


def ping_device(ip_address):
    """
    Ping a device 5 times using fping.
    
    Args:
        ip_address (str): IP address to ping
        
    Returns:
        tuple: (is_alive: bool, successful_count: int)
        Device is alive if 3 or more pings succeed
    """
    try:
        # fping -c 5: send 5 pings
        # -t 1000: 1 second timeout per ping
        # -q: quiet (only show summary)
        command = ["fping", "-c", "5", "-t", "1000", "-q", ip_address]
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        
        # Parse stderr for results (fping outputs to stderr)
        stderr = result.stderr.decode('utf-8')
        
        # Example stderr: "8.8.8.8 : xmt/rcv/%loss = 5/5/0%, min/avg/max = 23.3/119/152"
        # We need the first part: xmt/rcv/%loss
        if 'xmt/rcv/%loss' in stderr and '=' in stderr:
            # Get the part between first = and next comma (or end)
            stats_part = stderr.split('xmt/rcv/%loss =')[1].split(',')[0].strip()
            parts = stats_part.split('/')
            logger.debug(f"Ping stats for {ip_address}: {stats_part}")
            if len(parts) >= 2:
                sent = int(parts[0])
                received = int(parts[1])
                is_alive = received >= 3  # 3 or more successes
                return is_alive, received
        
        return False, 0
        
    except subprocess.TimeoutExpired:
        logger.warning(f"Ping timeout for {ip_address}")
        return False, 0
    except FileNotFoundError:
        logger.exception("fping not found. Install with: apt-get install fping")
        return False, 0
    except Exception as e:
        logger.exception(f"Error pinging {ip_address}: {e}")
        return False, 0


def ping_devices_batch(ip_addresses: List[str], batch_size: int = 10) -> Dict[str, Tuple[bool, int]]:
    """
    Ping multiple devices using fping's multi-host mode for better performance.
    
    Args:
        ip_addresses (List[str]): List of IP addresses to ping
        batch_size (int): Maximum number of devices to ping in one batch (default: 10)
        
    Returns:
        Dict[str, Tuple[bool, int]]: Mapping of IP -> (is_alive, successful_count)
    """
    results = {}
    
    # Process in batches to avoid command line length limits
    for i in range(0, len(ip_addresses), batch_size):
        batch = ip_addresses[i:i + batch_size]
        batch_results = _ping_batch(batch)
        results.update(batch_results)
    
    return results


def _ping_batch(ip_addresses: List[str]) -> Dict[str, Tuple[bool, int]]:
    """
    Ping a batch of devices using fping's multi-host mode.
    
    Args:
        ip_addresses (List[str]): List of IP addresses to ping
        
    Returns:
        Dict[str, Tuple[bool, int]]: Mapping of IP -> (is_alive, successful_count)
    """
    results = {}
    
    try:
        # Create temporary file with IP addresses
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('\n'.join(ip_addresses))
            temp_file = f.name
        
        try:
            # fping -f: read targets from file
            # -c 5: send 5 pings per target
            # -t 1000: 1 second timeout per ping
            # -q: quiet (only show summary)
            command = ["fping", "-f", temp_file, "-c", "5", "-t", "1000", "-q"]
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30  # Longer timeout for batch
            )
            
            # Parse results from stderr
            stderr = result.stderr.decode('utf-8')
            results = _parse_fping_batch_output(stderr, ip_addresses)
            
        finally:
            # Clean up temp file
            import os
            os.unlink(temp_file)
            
    except subprocess.TimeoutExpired:
        logger.warning(f"Ping batch timeout for {len(ip_addresses)} devices")
        # Mark all as failed
        for ip in ip_addresses:
            results[ip] = (False, 0)
    except FileNotFoundError:
        logger.error("fping not found. Install with: apt-get install fping")
        # Mark all as failed
        for ip in ip_addresses:
            results[ip] = (False, 0)
    except Exception as e:
        logger.error(f"Error pinging batch: {e}")
        # Mark all as failed
        for ip in ip_addresses:
            results[ip] = (False, 0)
    
    return results


def _parse_fping_batch_output(stderr: str, expected_ips: List[str]) -> Dict[str, Tuple[bool, int]]:
    """
    Parse fping batch output to extract results for each IP.
    
    Args:
        stderr (str): fping stderr output
        expected_ips (List[str]): List of IPs that were pinged
        
    Returns:
        Dict[str, Tuple[bool, int]]: Mapping of IP -> (is_alive, successful_count)
    """
    results = {}
    
    # Initialize all IPs as failed
    for ip in expected_ips:
        results[ip] = (False, 0)
    
    # Parse each line in the output
    lines = stderr.strip().split('\n')
    for line in lines:
        if 'xmt/rcv/%loss' in line and '=' in line:
            try:
                # Extract IP address (first part before colon)
                ip_part = line.split(':')[0].strip()
                
                # Extract stats part
                stats_part = line.split('xmt/rcv/%loss =')[1].split(',')[0].strip()
                parts = stats_part.split('/')
                
                if len(parts) >= 2:
                    sent = int(parts[0])
                    received = int(parts[1])
                    is_alive = received >= 3  # 3 or more successes
                    
                    if ip_part in results:
                        results[ip_part] = (is_alive, received)
                        logger.debug(f"Ping stats for {ip_part}: {stats_part}")
                        
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse fping output line: {line} - {e}")
                continue
    
    return results


def ping_devices_with_fallback(ip_addresses: List[str], batch_size: int = 10) -> Dict[str, Tuple[bool, int]]:
    """
    Ping devices using batch mode, with fallback to individual pings if batch fails.
    
    Args:
        ip_addresses (List[str]): List of IP addresses to ping
        batch_size (int): Maximum number of devices to ping in one batch
        
    Returns:
        Dict[str, Tuple[bool, int]]: Mapping of IP -> (is_alive, successful_count)
    """
    try:
        # Try batch approach first
        logger.debug(f"Attempting batch ping for {len(ip_addresses)} devices")
        results = ping_devices_batch(ip_addresses, batch_size)
        
        # Check if batch was successful (at least some results)
        successful_results = sum(1 for is_alive, count in results.values() if count > 0)
        
        if successful_results == 0 and len(ip_addresses) > 0:
            logger.warning("Batch ping failed completely, falling back to individual pings")
            # Fall back to individual pings
            results = {}
            for ip in ip_addresses:
                try:
                    results[ip] = ping_device(ip)
                except Exception as e:
                    logger.exception(f"Individual ping failed for {ip}: {e}")
                    results[ip] = (False, 0)
        else:
            logger.debug(f"Batch ping successful: {successful_results}/{len(ip_addresses)} devices responded")
            
    except Exception as e:
        logger.exception(f"Batch ping failed with error: {e}, falling back to individual pings")
        # Fall back to individual pings
        results = {}
        for ip in ip_addresses:
            try:
                results[ip] = ping_device(ip)
            except Exception as e:
                logger.exception(f"Individual ping failed for {ip}: {e}")
                results[ip] = (False, 0)
    
    return results


"""
VPN Network Loader Utility

This module provides functionality to load VPN CIDR ranges from a text file
into Redis for fast lookups during traffic classification.

Follows the same pattern as dns_loader.py - uses Redis directly.
"""

import os
import logging
import uuid
import ipaddress
from typing import Tuple, Set, Optional, List
from django.conf import settings
import redis

logger = logging.getLogger(__name__)

# Redis configuration - same as DNS pattern
REDIS_VPN_KEY = "vpn_networks:cidr_set"


class VPNNetworkLoader:
    """Utility class for loading VPN CIDR ranges from text file into Redis"""
    
    def __init__(self, txt_path: Optional[str] = None, redis_conn: Optional[redis.Redis] = None):
        """
        Initialize VPN loader
        
        Args:
            txt_path: Path to vpn-ipv4.txt file (defaults to data/vpn-ipv4.txt)
            redis_conn: Existing Redis connection (optional, will create if not provided)
        """
        if txt_path is None:
            # Default path relative to control_center directory
            self.txt_path = os.path.join(
                settings.BASE_DIR,
                'data',
                'vpn-ipv4.txt'
            )
        else:
            self.txt_path = txt_path
        
        # Use provided Redis connection or create new one
        if redis_conn:
            self.redis_conn = redis_conn
        else:
            redis_host = getattr(settings, 'CHANNEL_REDIS_HOST', 'redis')
            redis_port = getattr(settings, 'CHANNEL_REDIS_PORT', 6379)
            self.redis_conn = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_timeout=5,           # 5 second timeout for operations
                socket_connect_timeout=5,   # 5 second timeout for connection
                retry_on_timeout=True,      # Automatically retry once on timeout
            )
        
        # Cache for sorted networks (loaded on first access)
        self._sorted_networks: Optional[List[ipaddress.IPv4Network]] = None

    
    def load_vpn_networks(self, batch_size: int = 1000) -> Tuple[bool, int, str]:
        """
        Load VPN CIDR ranges from text file into Redis
        
        Uses atomic rename pattern: loads into temp key, then atomically
        replaces the production key on success to ensure zero-downtime updates.
        
        Args:
            batch_size: Number of CIDR ranges to add to Redis in each batch (default: 1000)
            
        Returns:
            Tuple of (success: bool, count: int, message: str)
        """
        if not os.path.exists(self.txt_path):
            error_msg = f"VPN networks file not found: {self.txt_path}"
            logger.error(error_msg)
            return False, 0, error_msg
        
        # Create temporary key for atomic update
        temp_key = f"{REDIS_VPN_KEY}:tmp:{uuid.uuid4()}"
        
        try:
            logger.info(f"Loading VPN networks from: {self.txt_path}")
            logger.info(f"Using temporary key: {temp_key}")
            
            cidr_ranges = set()  # Use set to avoid duplicates
            total_count = 0
            batch_count = 0
            invalid_count = 0
            
            with open(self.txt_path, 'r', encoding='utf-8') as txtfile:
                for line_num, line in enumerate(txtfile, 1):
                    cidr = line.strip()
                    
                    # Skip empty lines
                    if not cidr:
                        continue
                    
                    # Validate CIDR range
                    try:
                        # This will raise ValueError if CIDR is invalid
                        network = ipaddress.IPv4Network(cidr, strict=False)
                        # Normalize CIDR (e.g., "192.168.1.1/24" -> "192.168.1.0/24")
                        normalized_cidr = str(network)
                        
                        # Add to current batch
                        cidr_ranges.add(normalized_cidr)
                        
                    except (ValueError, ipaddress.AddressValueError) as e:
                        invalid_count += 1
                        logger.warning(f"Invalid CIDR range at line {line_num}: {cidr} - {e}")
                        continue
                    
                    # When batch is full, add to Redis using SADD to temp key
                    if len(cidr_ranges) >= batch_size:
                        self.redis_conn.sadd(temp_key, *cidr_ranges)
                        total_count += len(cidr_ranges)
                        batch_count += 1
                        logger.info(f"Batch {batch_count}: Added {len(cidr_ranges)} VPN networks (Total: {total_count})")
                        cidr_ranges.clear()
                
                # Add remaining CIDR ranges
                if cidr_ranges:
                    self.redis_conn.sadd(temp_key, *cidr_ranges)
                    total_count += len(cidr_ranges)
                    batch_count += 1
                    logger.info(f"Final batch {batch_count}: Added {len(cidr_ranges)} VPN networks (Total: {total_count})")
            
            # Verify count in temp key
            redis_count = self.redis_conn.scard(temp_key)
            logger.info(f"Loaded {redis_count} VPN CIDR ranges into temporary key")
            
            if invalid_count > 0:
                logger.warning(f"Skipped {invalid_count} invalid CIDR ranges")
            
            # Ensure we have data to rename
            if total_count == 0:
                error_msg = "No valid CIDR ranges found in file"
                logger.error(error_msg)
                try:
                    self.redis_conn.delete(temp_key)
                except Exception:
                    pass
                return False, 0, error_msg
            
            # Atomically replace production key with temp key
            self.redis_conn.rename(temp_key, REDIS_VPN_KEY)
            logger.info(f"Atomically replaced {REDIS_VPN_KEY} with new data")
            
            success_msg = f"Successfully loaded {redis_count} VPN CIDR ranges into Redis from {total_count} entries"
            logger.info(success_msg)
            
            return True, redis_count, success_msg
            
        except Exception as e:
            # Cleanup temp key on failure
            try:
                self.redis_conn.delete(temp_key)
                logger.info(f"Cleaned up temporary key: {temp_key}")
            except Exception as cleanup_error:
                logger.exception(f"Error cleaning up temporary key {temp_key}: {cleanup_error}")
            
            error_msg = f"Error loading VPN networks: {e}"
            logger.exception(error_msg)
            return False, 0, error_msg
    
    def _load_networks_cache(self) -> List[ipaddress.IPv4Network]:
        """
        Load and cache sorted networks from Redis for efficient binary search.
        Networks are cached in memory to avoid repeated Redis lookups.
        
        Returns:
            Sorted list of IPv4Network objects
        """
        # Check if cache is still valid (reload if Redis key was updated)
        try:
            # Get all CIDR ranges from Redis
            cidr_ranges = self.redis_conn.smembers(REDIS_VPN_KEY)
            
            # Convert to IPv4Network objects and sort by network address
            networks = []
            for cidr in cidr_ranges:
                try:
                    network = ipaddress.IPv4Network(cidr, strict=False)
                    networks.append(network)
                except (ValueError, ipaddress.AddressValueError):
                    logger.warning(f"Invalid CIDR range in Redis: {cidr}")
                    continue
            
            # Sort by network address for efficient binary search
            networks.sort(key=lambda n: int(n.network_address))
            
            self._sorted_networks = networks
            logger.debug(f"Cached {len(networks)} VPN networks for efficient lookup")
            return networks
            
        except Exception as e:
            logger.exception(f"Error loading VPN networks cache: {e}")
            return []
    
    def verify_vpn_ip(self, ip_address: str) -> bool:
        """
        Verify if a specific IP address falls within any VPN CIDR range stored in Redis.
        Uses binary search on sorted networks for O(log n) lookup performance.
        
        Args:
            ip_address: IP address to check
            
        Returns:
            bool: True if IP is in any VPN CIDR range, False otherwise
        """
        try:
            # Validate IP address
            ip = ipaddress.IPv4Address(ip_address)
            ip_int = int(ip)
            
            # Load networks cache if not already loaded
            if self._sorted_networks is None:
                self._sorted_networks = self._load_networks_cache()
            
            if not self._sorted_networks:
                return False
            
            # Use binary search to find potential matches
            # Since networks are sorted by network_address, we can use bisect
            # to find networks where network_address <= ip <= broadcast_address
            
            # Find insertion point for IP (networks sorted by network_address)
            # We need to check networks that could contain this IP
            # A network contains IP if: network_address <= IP <= broadcast_address
            
            # Binary search for networks that start before or at our IP
            # Then check if IP falls within any of those networks
            networks = self._sorted_networks
            
            # Find the rightmost network where network_address <= IP
            # This gives us a starting point to check
            left = 0
            right = len(networks) - 1
            best_idx = -1
            counter = 0
            
            while left <= right:
                counter += 1
                mid = (left + right) // 2
                if int(networks[mid].network_address) <= ip_int:
                    best_idx = mid
                    left = mid + 1
                else:
                    right = mid - 1
            logger.debug(f" [VPN Loader] Binary search completed in {counter} iterations.")
            # Check networks backwards from best_idx
            # Since networks are sorted by network_address and best_idx is the rightmost
            # network where network_address <= ip_int, all networks we check will have
            # network_address <= ip_int, so we only need to check if IP is within broadcast_address
            for i in range(best_idx, -1, -1):
                network = networks[i]
                # Check if IP is in this network (network_address <= IP <= broadcast_address)
                if ip_int <= int(network.broadcast_address) and ip in network:
                    return True
            
            return False
            
        except (ValueError, ipaddress.AddressValueError) as e:
            logger.warning(f"Invalid IP address for VPN check: {ip_address} - {e}")
            return False
        except Exception as e:
            logger.exception(f" [VPN Loader] Error verifying VPN IP: {e}. Fallback to simple iteration.")
            # Fallback to simple iteration if binary search fails
            try:
                cidr_ranges = self.redis_conn.smembers(REDIS_VPN_KEY)
                ip = ipaddress.IPv4Address(ip_address)
                for cidr in cidr_ranges:
                    try:
                        network = ipaddress.IPv4Network(cidr, strict=False)
                        if ip in network:
                            return True
                    except (ValueError, ipaddress.AddressValueError):
                        continue
            except Exception:
                pass
            return False
    
    def get_vpn_count(self) -> int:
        """
        Get the count of VPN CIDR ranges in Redis
        
        Returns:
            int: Number of VPN CIDR ranges stored
        """
        try:
            return self.redis_conn.scard(REDIS_VPN_KEY)
        except Exception as e:
            logger.exception(f"Error getting VPN count from Redis: {e}")
            return 0
    
    def get_cache_status(self) -> dict:
        """
        Get the status of the in-memory network cache.
        
        Returns:
            dict: Dictionary with 'is_loaded' (bool) and 'count' (int) keys.
                  'is_loaded' indicates if cache is populated, 'count' is the
                  number of networks in cache (0 if not loaded or empty).
        """
        if self._sorted_networks is None:
            return {'is_loaded': False, 'count': 0}
        return {'is_loaded': True, 'count': len(self._sorted_networks)}
    
    def get_sample_vpn_networks(self, count: int = 10) -> Set[str]:
        """
        Get a sample of VPN CIDR ranges from the file (for testing/verification)
        
        Args:
            count: Number of sample CIDR ranges to retrieve
            
        Returns:
            Set of sample CIDR ranges
        """
        sample_cidrs = set()
        
        try:
            with open(self.txt_path, 'r', encoding='utf-8') as txtfile:
                for i, line in enumerate(txtfile):
                    if i >= count:
                        break
                    
                    cidr = line.strip()
                    if cidr:
                        try:
                            # Validate and normalize
                            network = ipaddress.IPv4Network(cidr, strict=False)
                            sample_cidrs.add(str(network))
                        except (ValueError, ipaddress.AddressValueError):
                            continue
                        
        except Exception as e:
            logger.exception(f"Error getting sample VPN networks: {e}")
        
        return sample_cidrs


# Global VPN loader instance
vpn_loader = VPNNetworkLoader()


"""
DNS Server Loader Utility

This module provides functionality to load DNS server IPs from a CSV file
into Redis for fast O(1) lookups during traffic classification.

Follows the same pattern as populate_redis_asn.py - uses Redis directly.
"""

import csv
import os
import logging
from typing import Tuple, Set
from django.conf import settings
import redis

logger = logging.getLogger(__name__)

# Redis configuration - same as ASN pattern
REDIS_DNS_KEY = "dns_servers:ip_set"


class DNSServerLoader:
    """Utility class for loading DNS servers from CSV into Redis"""
    
    def __init__(self, csv_path: str = None, redis_conn: redis.Redis = None):
        """
        Initialize DNS loader
        
        Args:
            csv_path: Path to nameservers.csv file (defaults to data/nameservers.csv)
            redis_conn: Existing Redis connection (optional, will create if not provided)
        """
        if csv_path is None:
            # Default path relative to control_center directory
            self.csv_path = os.path.join(
                settings.BASE_DIR,
                'data',
                'nameservers.csv'
            )
        else:
            self.csv_path = csv_path
        
        # Use provided Redis connection or create new one
        if redis_conn:
            self.redis_conn = redis_conn
        else:
            redis_host = getattr(settings, 'CHANNEL_REDIS_HOST', 'redis')
            redis_port = getattr(settings, 'CHANNEL_REDIS_PORT', 6379)
            self.redis_conn = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True
            )
    
    def load_dns_servers(self, batch_size: int = 1000) -> Tuple[bool, int, str]:
        """
        Load DNS server IPs from CSV file into Redis
        
        Args:
            batch_size: Number of IPs to add to Redis in each batch (default: 1000)
            
        Returns:
            Tuple of (success: bool, count: int, message: str)
        """
        if not os.path.exists(self.csv_path):
            error_msg = f"DNS servers CSV file not found: {self.csv_path}"
            logger.error(error_msg)
            return False, 0, error_msg
        
        try:
            logger.info(f"Loading DNS servers from: {self.csv_path}")
            
            # Clear existing DNS servers first (like ASN pattern)
            self.redis_conn.delete(REDIS_DNS_KEY)
            logger.info("Cleared existing DNS servers from Redis")
            
            ip_addresses = set()  # Use set to avoid duplicates
            total_count = 0
            batch_count = 0
            
            with open(self.csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    ip_address = row.get('ip_address', '').strip()
                    
                    # Skip empty IPs or invalid entries
                    if not ip_address or ip_address == '':
                        continue
                    
                    # Add to current batch
                    ip_addresses.add(ip_address)
                    
                    # When batch is full, add to Redis using SADD (Redis SET)
                    if len(ip_addresses) >= batch_size:
                        self.redis_conn.sadd(REDIS_DNS_KEY, *ip_addresses)
                        total_count += len(ip_addresses)
                        batch_count += 1
                        logger.info(f"Batch {batch_count}: Added {len(ip_addresses)} DNS servers (Total: {total_count})")
                        ip_addresses.clear()
                
                # Add remaining IPs
                if ip_addresses:
                    self.redis_conn.sadd(REDIS_DNS_KEY, *ip_addresses)
                    total_count += len(ip_addresses)
                    batch_count += 1
                    logger.info(f"Final batch {batch_count}: Added {len(ip_addresses)} DNS servers (Total: {total_count})")
            
            # Verify count in Redis using SCARD (like ZCARD for ASN)
            redis_count = self.redis_conn.scard(REDIS_DNS_KEY)
            success_msg = f"Successfully loaded {redis_count} DNS server IPs into Redis from {total_count} entries"
            logger.info(success_msg)
            
            return True, redis_count, success_msg
            
        except Exception as e:
            error_msg = f"Error loading DNS servers: {e}"
            logger.error(error_msg, exc_info=True)
            return False, 0, error_msg
    
    def get_sample_dns_servers(self, count: int = 10) -> Set[str]:
        """
        Get a sample of DNS server IPs from the CSV (for testing/verification)
        
        Args:
            count: Number of sample IPs to retrieve
            
        Returns:
            Set of sample IP addresses
        """
        sample_ips = set()
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for i, row in enumerate(reader):
                    if i >= count:
                        break
                    
                    ip_address = row.get('ip_address', '').strip()
                    if ip_address:
                        sample_ips.add(ip_address)
                        
        except Exception as e:
            logger.error(f"Error getting sample DNS servers: {e}")
        
        return sample_ips
    
    def verify_dns_server(self, ip_address: str) -> bool:
        """
        Verify if a specific IP is loaded in Redis as a DNS server
        
        Args:
            ip_address: IP address to check
            
        Returns:
            bool: True if IP is in Redis, False otherwise
        """
        try:
            return self.redis_conn.sismember(REDIS_DNS_KEY, ip_address)
        except Exception as e:
            logger.error(f"Error verifying DNS server in Redis: {e}")
            return False
    
    def get_dns_count(self) -> int:
        """
        Get the count of DNS servers in Redis
        
        Returns:
            int: Number of DNS server IPs stored
        """
        try:
            return self.redis_conn.scard(REDIS_DNS_KEY)
        except Exception as e:
            logger.error(f"Error getting DNS count from Redis: {e}")
            return 0


# Global DNS loader instance
dns_loader = DNSServerLoader()


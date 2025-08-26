"""
IP-to-ASN Lookup Service

This module provides high-performance IP address to Autonomous System Number (ASN) lookup
functionality using Redis as the backend database. The service uses a Redis Sorted Set
where the score is the end IP address (integer) and the member contains the start IP,
ASN, and organization information.

Usage:
    from utils.ip_lookup_service import get_asn_from_ip
    
    result = get_asn_from_ip("8.8.8.8")
    if result:
        print(f"ASN: {result['asn']}, Organization: {result['organization']}")
    else:
        print("IP not found in ASN database")
"""

import ipaddress
import redis
from django.conf import settings
from typing import Optional, Dict, Union


# Redis configuration constants
REDIS_KEY = 'ip_asn_map'
REDIS_HOST = getattr(settings, 'CHANNEL_REDIS_HOST', 'redis')
REDIS_PORT = getattr(settings, 'CHANNEL_REDIS_PORT', 6379)


def get_asn_from_ip(ip_string: str) -> Optional[Dict[str, Union[int, str]]]:
    """
    Look up the ASN and organization information for a given IP address.
    
    This function performs a high-performance lookup using Redis Sorted Set.
    The lookup algorithm:
    1. Converts the IP to integer representation
    2. Finds the first range whose end IP (score) >= query IP
    3. Verifies the query IP is within the range (start IP <= query IP <= end IP)
    
    Args:
        ip_string (str): The IP address to look up (e.g., "8.8.8.8")
        
    Returns:
        Optional[Dict[str, Union[int, str]]]: Dictionary containing ASN and organization
        information if found, None if not found or invalid IP.
        
        Example return value:
        {
            'asn': 15169,
            'organization': 'GOOGLE'
        }
        
    Raises:
        redis.RedisError: If there's an issue connecting to or querying Redis
        ValueError: If the IP address format is invalid
        
    Example:
        >>> result = get_asn_from_ip("8.8.8.8")
        >>> print(result)
        {'asn': 15169, 'organization': 'GOOGLE'}
        
        >>> result = get_asn_from_ip("192.168.1.1")
        >>> print(result)
        None  # Private IP not in database
    """
    try:
        # Step 1: Validate and convert IP address
        ip_addr = ipaddress.ip_address(ip_string)
        ip_int = int(ip_addr)
        
    except ValueError:
        # Invalid IP address format
        return None
    
    try:
        # Step 2: Connect to Redis
        redis_conn = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )
        
        # Step 3: Query the Sorted Set for the first range whose end IP >= our IP
        result = redis_conn.zrangebyscore(
            REDIS_KEY,
            min=ip_int,
            max='+inf',
            start=0,
            num=1,
            withscores=True
        )
        
        # Step 4: Check if result is empty
        if not result:
            # IP was not found in any range
            return None
        
        # Step 5: Process the result
        # result is a list of tuples: [(member, score), ...]
        member, end_ip_score = result[0]
        
        # Decode the member string and split by colon
        # Format: "start_ip_int:asn:organization"
        parts = member.split(':')
        
        if len(parts) != 3:
            # Invalid member format
            return None
        
        start_ip_str, asn_str, organization = parts
        
        # Convert start IP string to integer
        try:
            start_ip_int = int(start_ip_str)
            asn = int(asn_str)
        except ValueError:
            # Invalid integer conversion
            return None
        
        # Step 6: Final verification - check if IP is within the range
        if start_ip_int <= ip_int <= int(end_ip_score):
            return {
                'asn': asn,
                'organization': organization
            }
        else:
            # IP falls into a gap between defined ranges
            return None
            
    except redis.RedisError as e:
        # Re-raise Redis errors for proper error handling by caller
        raise redis.RedisError(f"Redis connection/query error: {e}")
    except Exception as e:
        # Catch any other unexpected errors
        raise ValueError(f"Unexpected error during IP lookup: {e}")


def get_asn_from_ip_safe(ip_string: str) -> Optional[Dict[str, Union[int, str]]]:
    """
    Safe version of get_asn_from_ip that catches all exceptions and returns None.
    
    This function is useful when you want to handle lookup failures gracefully
    without exception handling in the calling code.
    
    Args:
        ip_string (str): The IP address to look up
        
    Returns:
        Optional[Dict[str, Union[int, str]]]: ASN information if found, None otherwise
        
    Example:
        >>> result = get_asn_from_ip_safe("8.8.8.8")
        >>> print(result)
        {'asn': 15169, 'organization': 'GOOGLE'}
        
        >>> result = get_asn_from_ip_safe("invalid-ip")
        >>> print(result)
        None
    """
    try:
        return get_asn_from_ip(ip_string)
    except Exception:
        # Catch all exceptions and return None
        return None


def test_lookup_service():
    """
    Test function to verify the lookup service is working correctly.
    
    This function tests various IP addresses including known public IPs
    and private IPs to ensure the service behaves as expected.
    """
    test_cases = [
        ("8.8.8.8", "Google DNS"),
        ("1.1.1.1", "Cloudflare DNS"),
        ("208.67.222.222", "OpenDNS"),
        ("192.168.1.1", "Private IP (should return None)"),
        ("10.0.0.1", "Private IP (should return None)"),
        ("172.16.0.1", "Private IP (should return None)"),
        ("invalid-ip", "Invalid IP (should return None)"),
    ]
    
    print("Testing IP-to-ASN Lookup Service")
    print("=" * 50)
    
    for ip, description in test_cases:
        try:
            result = get_asn_from_ip(ip)
            if result:
                print(f"✅ {ip} ({description}) -> ASN: {result['asn']}, Org: {result['organization']}")
            else:
                print(f"❌ {ip} ({description}) -> Not found")
        except Exception as e:
            print(f"❌ {ip} ({description}) -> Error: {e}")
    
    print("=" * 50)
    print("Test completed")


if __name__ == "__main__":
    # Run tests if module is executed directly
    test_lookup_service()

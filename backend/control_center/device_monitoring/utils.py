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
            logger.info(f"Ping stats for {ip_address}: {stats_part}")
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
        logger.error("fping not found. Install with: apt-get install fping")
        return False, 0
    except Exception as e:
        logger.error(f"Error pinging {ip_address}: {e}")
        return False, 0


#!/usr/bin/env python
# File: test_playbook.py
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

"""
Test Playbook Runner

This script allows you to easily test ansible playbooks using variables from a .env file.
Place a .env file in the utils folder with the following variables:
    IP=<device_ip>
    USER=<device_username>
    PASSWORD=<device_password>

Usage:
    python test_playbook.py

Then modify the main() function to test different playbooks.
"""

import os
import sys
import pathlib
from dotenv import load_dotenv
import logging
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path to allow imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from utils.ansible_formtter import (
    get_interfaces_from_results, 
    get_filtered_interfaces, 
    extract_ovs_port_map,
    get_interface_speeds_from_results
)
from utils.ansible_utils import run_playbook_with_extravars, create_temp_inv, create_inv_data


def print_result(title, data, indent=2):
    """Pretty print results"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(json.dumps(data, indent=indent))
    print(f"{'='*60}\n")


def test_get_ports(ip, user, password, playbook_dir):
    """Test the get-ports playbook"""
    logger.info("Testing get-ports playbook...")
    
    inv_content = create_inv_data(ip, user, password)
    inv_path = create_temp_inv(inv_content)
    
    result = run_playbook_with_extravars('get-ports', playbook_dir, inv_path)
    
    interfaces = get_interfaces_from_results(result.get('results', {}))
    logger.info(f"Interfaces found: {interfaces}")
    
    return result


def test_get_ports_ip_link(ip, user, password, playbook_dir):
    """Test the get-ports-ip-link playbook"""
    logger.info("Testing get-ports-ip-link playbook...")
    
    inv_content = create_inv_data(ip, user, password)
    inv_path = create_temp_inv(inv_content)
    
    result = run_playbook_with_extravars('get-ports-ip-link', playbook_dir, inv_path)
    
    interfaces = get_filtered_interfaces(result)
    speeds = get_interface_speeds_from_results(result)
    
    logger.info(f"Filtered interfaces: {interfaces}")
    logger.info(f"Interface speeds: {speeds}")
    
    return result


def test_ovs_port_numbers(ip, user, password, playbook_dir, bridge_name, ports):
    """Test the get-ovs-port-numbers playbook"""
    logger.info(f"Testing get-ovs-port-numbers for bridge {bridge_name}...")
    
    inv_content = create_inv_data(ip, user, password)
    inv_path = create_temp_inv(inv_content)
    
    result = run_playbook_with_extravars(
        'get-ovs-port-numbers',
        playbook_dir,
        inv_path,
        {
            'interfaces': ports,
            'ip_address': ip,
            'bridge_name': bridge_name
        },
        quiet=False
    )
    
    ovs_port_map = extract_ovs_port_map(result)
    logger.info(f"OVS Port Map: {ovs_port_map}")
    
    return result


def test_ovs_show(ip, user, password, playbook_dir):
    """Test the ovs-show playbook"""
    logger.info("Testing ovs-show playbook...")
    
    inv_content = create_inv_data(ip, user, password)
    inv_path = create_temp_inv(inv_content)
    
    result = run_playbook_with_extravars('ovs-show', playbook_dir, inv_path)
    
    return result


def test_custom_playbook(ip, user, password, playbook_dir, playbook_name, extra_vars=None):
    """Test any custom playbook with optional extra variables"""
    logger.info(f"Testing {playbook_name} playbook...")
    
    inv_content = create_inv_data(ip, user, password)
    inv_path = create_temp_inv(inv_content)
    
    if extra_vars:
        result = run_playbook_with_extravars(
            playbook_name,
            playbook_dir,
            inv_path,
            extra_vars,
            quiet=False
        )
    else:
        result = run_playbook_with_extravars(playbook_name, playbook_dir, inv_path)
    
    return result


def main():
    # Load .env file from the same directory as this script
    env_path = os.path.join(script_dir, '.env')
    if not os.path.exists(env_path):
        logger.error(f".env file not found at {env_path}")
        logger.info("Please create a .env file in the utils folder with IP, USER, and PASSWORD variables")
        sys.exit(1)
    
    load_dotenv(env_path)
    
    ip = os.getenv("IP")
    user = os.getenv("USER")
    password = os.getenv("PASSWORD")
    
    if not all([ip, user, password]):
        logger.error("Missing required environment variables. Please ensure IP, USER, and PASSWORD are set in .env file")
        sys.exit(1)
    
    logger.info(f"Connecting to {ip} as {user}")
    
    # Set playbook directory path
    ansible_dir = os.path.join(parent_dir, 'ansible', 'playbooks')
    
    # ========================================
    # MODIFY THIS SECTION TO TEST DIFFERENT PLAYBOOKS
    # ========================================
    
    # Example 1: Test get-ports-ip-link (with speed detection)
    result = test_get_ports_ip_link(ip, user, password, ansible_dir)
    print_result("GET-PORTS-IP-LINK RESULT", result)
    
    # Example 2: Test OVS port numbers
    # Uncomment and modify as needed:
    # bridge_name = 'br0'
    # ports = ['eth1', 'eth2']
    # result = test_ovs_port_numbers(ip, user, password, ansible_dir, bridge_name, ports)
    # print_result("OVS PORT NUMBERS RESULT", result)
    
    # Example 3: Test ovs-show
    # result = test_ovs_show(ip, user, password, ansible_dir)
    # print_result("OVS-SHOW RESULT", result)
    
    # Example 4: Test custom playbook with extra vars
    # result = test_custom_playbook(
    #     ip, user, password, ansible_dir, 
    #     'your-playbook-name',
    #     extra_vars={'bridge_name': 'br0', 'some_var': 'value'}
    # )
    # print_result("CUSTOM PLAYBOOK RESULT", result)
    
    logger.info("Testing complete!")


if __name__ == '__main__':
    main()


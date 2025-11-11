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
    get_interface_speeds_from_results,
    get_single_port_speed_from_results,
    get_port_status_from_results
)
from utils.ansible_utils import run_playbook_with_extravars, create_temp_inv, create_inv_data


def print_result(title, data, indent=2):
    """
    Prints a titled, delimited JSON representation of `data` to stdout.
    
    Parameters:
        title (str): Heading text displayed above the JSON output.
        data: A JSON-serializable Python object to be printed.
        indent (int): Number of spaces used for JSON indentation (default: 2).
    """
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(json.dumps(data, indent=indent))
    print(f"{'='*60}\n")


def test_get_ports(ip, user, password, playbook_dir):
    """
    Run the "get-ports" Ansible playbook using the provided connection credentials and playbook directory.
    
    Parameters:
        ip (str): Target host IP address to include in the temporary inventory.
        user (str): SSH username for the target host.
        password (str): SSH password for the target host.
        playbook_dir (str): Filesystem path to the directory containing the playbook.
    
    Returns:
        dict: Raw playbook execution result as returned by the playbook runner; includes a 'results' key used to extract interfaces.
    """
    logger.info("Testing get-ports playbook...")
    
    inv_content = create_inv_data(ip, user, password)
    inv_path = create_temp_inv(inv_content)
    
    result = run_playbook_with_extravars('get-ports', playbook_dir, inv_path)
    
    interfaces = get_interfaces_from_results(result.get('results', {}))
    logger.info(f"Interfaces found: {interfaces}")
    
    return result


def test_get_ports_ip_link(ip, user, password, playbook_dir):
    """
    Run the `get-ports-ip-link` Ansible playbook against a temporary inventory and log the filtered interfaces and their speeds.
    
    Parameters:
        ip (str): IP address of the target host.
        user (str): SSH username for the target host.
        password (str): SSH password for the target host.
        playbook_dir (str): Filesystem path to the directory containing the playbooks.
    
    Returns:
        result: Raw result object returned by the playbook runner containing playbook execution details.
    """
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
    """
    Run the `get-ovs-port-numbers` playbook for a given bridge and interfaces and return the raw playbook result.
    
    @param bridge_name: Name of the OVS bridge to query.
    @param ports: Iterable of interface names to map to OVS port numbers.
    @returns: Raw result object returned by the playbook runner.
    """
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
    """
    Run the 'ovs-show' Ansible playbook using the provided connection credentials and playbook directory.
    
    Parameters:
        ip (str): Target host IP address used to build a temporary inventory.
        user (str): SSH username for the target host.
        password (str): SSH password for the target host.
        playbook_dir (str): Filesystem path to the directory containing the playbook.
    
    Returns:
        result (dict): Raw result object produced by executing the playbook.
    """
    logger.info("Testing ovs-show playbook...")
    
    inv_content = create_inv_data(ip, user, password)
    inv_path = create_temp_inv(inv_content)
    
    result = run_playbook_with_extravars('ovs-show', playbook_dir, inv_path)
    
    return result


def test_custom_playbook(ip, user, password, playbook_dir, playbook_name, extra_vars=None):
    """
    Run the specified Ansible playbook against a temporary inventory created from the given credentials.
    
    Parameters:
        ip (str): IP address used to build the temporary inventory.
        user (str): SSH username used to build the temporary inventory.
        password (str): SSH password used to build the temporary inventory.
        playbook_dir (str): Path to the directory containing the playbook.
        playbook_name (str): Playbook filename or relative path within playbook_dir to execute.
        extra_vars (dict, optional): Extra variables to pass to the playbook; when provided they are included in the execution.
    
    Returns:
        result (dict): The raw execution result returned by the playbook runner, containing task and host-level details.
    """
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

def test_check_port_details(ip, user, password, playbook_dir, port_name):
    """
    Run the `check-port-details` Ansible playbook against a temporary inventory and log the port speed and status.
    
    Parameters:
        ip (str): IP address of the target host.
        user (str): SSH username for the target host.
        password (str): SSH password for the target host.
        playbook_dir (str): Filesystem path to the directory containing the playbooks.
        port_name (str): Name of the port to check.
    
    Returns:
        result: Raw result object returned by the playbook runner containing playbook execution details.
    """
    logger.info(f"Testing check-port-details playbook for port {port_name}...")
    
    inv_content = create_inv_data(ip, user, password)
    inv_path = create_temp_inv(inv_content)
    
    result = run_playbook_with_extravars('check-port-details', playbook_dir, inv_path, {'port_name': port_name, 'ip_address': ip})
    
    port_speed = get_single_port_speed_from_results(result, port_name)
    port_status = get_port_status_from_results(result, port_name)
    
    logger.info(f"Port speed: {port_speed}")
    logger.info(f"Port status: {port_status}")
    
    return result


def main():
    """
    Load credentials from a .env file, validate required variables, run a selected Ansible playbook test, and print the results.
    
    This function locates a .env file alongside the script, loads environment variables, and ensures IP, USER, and PASSWORD are present. If validation fails, the process exits with status 1. It then sets the playbook directory and executes a chosen test helper (by default the get-ports-ip-link test), printing its output. Modify the marked section to run different playbook tests or supply different arguments.
    """
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
    # result = test_get_ports_ip_link(ip, user, password, ansible_dir)
    # print_result("GET-PORTS-IP-LINK RESULT", result)
    
    # Example 2: Test check-port-details (with speed and status detection)
    # NOTE: Change port_name to match an interface on your target device
    port_name = 'enx9ca2f4fc1e81'
    result = test_check_port_details(ip, user, password, ansible_dir, port_name)
    print_result("CHECK-PORT-DETAILS RESULT", result)
    
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


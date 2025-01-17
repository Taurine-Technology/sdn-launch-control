# File: connect_to_controller.py
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
Description:
This script is part of ovs-management-toolbox and is responsible for connecting an Open vSwitch (OVS) bridge to a specified
controller. It prompts the user to select a bridge and provide controller details, then applies the configuration
using Ansible playbooks.

This module is a part of the service 'connect-to-controller' in the main(.py) application.
"""

from ..ansible_tasks import run_playbook
from ..utils import (save_bridge_name_to_config, save_controller_port_to_config, save_controller_ip_to_config)
from ..ovs_results_format import format_ovs_show, format_ovs_get_controller


def connect_to_controller(playbook_dir_path, inventory_path, config_path):
    results = run_playbook("ovs-show", playbook_dir_path, inventory_path)
    bridges = format_ovs_show(results)
    # Convert dictionary keys to a list
    bridge_names = list(bridges.keys())
    print(f"The target device has the following bridges:")
    for idx, choice in enumerate(bridge_names, 1):
        print(f"{idx}. {choice}")
    input_str = input("Enter the number of the bridge you want to assign a controller to: ").strip()
    if input_str.lower() != 'exit':
        try:
            bridge_number = int(input_str)
            if 1 <= bridge_number <= len(bridge_names):
                bridge_name = bridge_names[bridge_number - 1]
                print(f"You selected: {bridge_name}")
            else:
                print("Invalid number. Please enter a number within the range.")
                return

        except ValueError:
            print("Invalid input. Please enter a number.")
            return
        except Exception as e:
            print(f"An unexpected error occurred trying to get the bridge name: {e}. Please try again.")
            return
    else:
        print("Exiting to the main menu.")
        return

    save_bridge_name_to_config(bridge_name, config_path)
    ip_controller = input("Enter the IP address of the controller: ")
    port = input("Enter the port the controller uses: ")

    save_controller_port_to_config(port, config_path)
    save_controller_ip_to_config(ip_controller, config_path)
    save_bridge_name_to_config(bridge_name, config_path)
    results = run_playbook('connect-to-controller', playbook_dir_path, inventory_path)
    controller_details = format_ovs_get_controller(results)

    if controller_details:
        ip_result = controller_details["ip"]
        port_result = controller_details["port"]
        print(f'Successfully connected bridge {bridge_name} to controller with IP {ip_result} on port {port_result}')
    else:
        print(f'Could not connect your controller with IP: {ip_controller}, port: {port} to bridge {bridge_name}')
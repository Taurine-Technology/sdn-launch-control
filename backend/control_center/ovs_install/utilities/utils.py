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

"""
Description:
This script provides various utility functions for interacting with and configuring an Open vSwitch (OVS) environment.
Functions include writing to an inventory file, updating configuration files, saving various settings to configuration,
gathering system details, and managing device logins. This script is essential for the automation tasks related to
OVS setup and management, facilitating the interactions between the Python environment and Ansible playbooks.

Key functionalities:
- Writing network device details to an inventory file for Ansible.
- Saving IP addresses, interfaces, controller details, and bridge names to a configuration file.
- Loading and updating device login details.
- Backing up device configurations.
- Extracting and displaying system details from Ansible playbook results.
"""
import os

import yaml


def write_to_inventory(ip, user, password, inventory_path):
    with open(inventory_path, 'w') as f:
        f.write(f"[localserver]\n")
        f.write(f"{ip} ansible_user='{user}' ansible_password='{password}' "
                f"ansible_ssh_common_args='-o StrictHostKeyChecking=no' ansible_become_pass='{password}'\n")


def update_config(data, config_path):
    # Read the existing YAML file
    with open(config_path, 'r') as file:
        existing_data = yaml.safe_load(file) or {}  # load the file or create an empty dictionary

    # Update the dictionary with new data
    existing_data.update(data)

    # Write the updated dictionary back to the YAML file
    with open(config_path, 'w') as file:
        yaml.safe_dump(existing_data, file)


def save_switch_id(switch_id, config_path):
    update_config({'switch_id': switch_id}, config_path)


def save_api_base_url(api_base_url, config_path):
    update_config({'api_base_url': api_base_url}, config_path)


def save_monitor_interface(monitor_interface, config_path):
    update_config({'monitor_interface': monitor_interface}, config_path)


def save_port_to_clients(port_to_clients, config_path):
    update_config({'port_to_clients': port_to_clients}, config_path)


def save_port_to_router(port_to_router, config_path):
    update_config({'port_to_router': port_to_router}, config_path)


def save_num_bytes(num_bytes, config_path):
    update_config({'num_bytes': num_bytes}, config_path)


def save_num_packets(num_packets, config_path):
    update_config({'num_packets': num_packets}, config_path)


def save_model_name(model_name, config_path):
    update_config({'model_name': model_name}, config_path)


def save_ip_to_config(ip, config_path):
    update_config({'ip_address': ip}, config_path)


def save_api_url_to_config(api_url, config_path):
    update_config({'api_url': api_url}, config_path)

def save_pi_bool(is_pi, config_path):
    update_config({'is_pi': is_pi}, config_path)

def save_openflow_version_to_config(openflow_version, config_path):
    update_config({'openflow_version': openflow_version}, config_path)


def save_interfaces_to_config(interfaces, config_path):
    update_config({'interfaces': interfaces}, config_path)


def save_controller_ip_to_config(ip, config_path):
    update_config({'controller_ip': ip}, config_path)


def save_controller_port_to_config(port, config_path):
    update_config({'controller_port': port}, config_path)


def save_bridge_name_to_config(name, config_path):
    update_config({'bridge_name': name}, config_path)


def get_os_from_results(results):
    results_key = 'results'
    if results.get(results_key):
        results = results[results_key]
    key = 'Get target system OS'
    target = 'ansible_distribution'
    results_to_return = {}
    # print('*** in get_os_from_results ***')
    # print(results)
    if results.get(key):
        results_dic = results[key]
        # print(results)
        os = results_dic[target]
        results_to_return['os'] = os
    key = 'Display OS Version'
    target = 'ansible_distribution_version'
    if results.get(key):
        results_dic = results[key]
        distribution = results_dic[target]
        results_to_return['distribution'] = distribution
    return results_to_return


def get_interfaces_from_results(results):
    key = 'Display Network Interfaces'

    target = 'ansible_interfaces'
    if results.get(key):
        results_dic = results[key]
        interfaces = results_dic[target]
        # print(interfaces)
        return interfaces


def check_system_details(results):
    interfaces_to_return = ''
    # print('*** in check_system_details ***')
    # print(results)
    results_key = 'results'
    if results.get(results_key):
        results = results[results_key]
    # print(results)
    os_details = get_os_from_results(results)
    interfaces_arr = get_interfaces_from_results(results)
    interfaces_to_return = interfaces_arr
    opr_system = 'Unknown'
    if os_details.get('os'):
        opr_system = os_details['os']
    distribution = 'Unknown'
    if os_details.get('distribution'):
        distribution = os_details['distribution']
    print()
    print(f"Your target device OS is {opr_system}, your target device distribution is {distribution} and you are "
          f"working with the following interfaces {interfaces_arr}.")
    print()
    if opr_system == 'Ubuntu' and distribution == '20.04':
        print("We have tested this code on this OS and distribution.")
    elif opr_system == 'Unknown':
        print('We could not identify the target OS.')
    else:
        print("We have not tested this code on your target OS. Please provide me with feedback on x.com "
              "@keeganwhitetech if it is successful or open an issue of GitHub if there are issues providing the"
              f"details below:\n OS: {opr_system}\Distribution: {distribution}")
    # print('returning')
    return interfaces_to_return


def save_device_login_to_yaml(yaml_file_path, name, ip, user, password):
    new_entry = {
        'name': name,
        'ip': ip,
        'user': user,
        'password': password
    }
    # Check if the YAML file exists
    if os.path.exists(yaml_file_path):
        # If the file exists, load the existing data
        with open(yaml_file_path, 'r') as file:
            data = yaml.safe_load(file)
        # Add the new entry to the list of checks
        data['login_details'].append(new_entry)
    else:
        # If the file does not exist, create a new data structure
        data = {'login_details': [new_entry]}

    # Save the data to the YAML file
    with open(yaml_file_path, 'w') as file:
        yaml.safe_dump(data, file)


def load_device_logins_from_yaml(yaml_file_path):
    # Check if the YAML file exists
    if os.path.exists(yaml_file_path):
        # If the file exists, load the existing data
        with open(yaml_file_path, 'r') as file:
            data = yaml.safe_load(file)
            return data
    else:
        # If the file does not exist, create a new data structure
        return None


def update_devices(device_name, bridges, user, password, ip, file_name):
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            data = yaml.safe_load(file)
            if data is None:
                data = {'devices': []}
    else:
        data = {'devices': []}

    # Check if device_name already exists
    existing_device = next((device for device in data['devices'] if device['device_name'] == device_name), None)
    while existing_device:
        choice = input(
            f"Device named '{device_name}' already exists. Do you want to overwrite it? (y/n): ").strip().lower()
        if choice == 'y':
            data['devices'].remove(existing_device)
            break
        else:
            device_name = input("Please provide another unique device name: ").strip()
            existing_device = next((device for device in data['devices'] if device['device_name'] == device_name), None)

    # Construct device data
    device = {
        'device_name': device_name,
        'active': True,  # Default to True
        'user_name': user,
        'password': password,
        'ip_address': ip,
    }

    # Construct OVS bridges data
    ovs_bridges = []
    for bridge, details in bridges.items():
        bridge_ports = [port for port in details['Ports'] if
                        port != bridge]  # Excluding port if it's same as bridge name
        bridge_data = {
            'bridge_name': bridge,
            'ports': [{'port_name': port} for port in bridge_ports]
        }
        ovs_bridges.append(bridge_data)

    device['ovs_bridges'] = ovs_bridges

    # Append new device to existing data
    data['devices'].append(device)

    # Save updated data back to file
    with open(file_name, 'w') as file:
        yaml.dump(data, file)

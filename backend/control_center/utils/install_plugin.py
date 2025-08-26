# File: install_plugin.py
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

from django.shortcuts import get_object_or_404
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status
import logging
from utils.ansible_utils import run_playbook_with_extravars, create_temp_inv, create_inv_data
from general.models import Device
from ovs_install.utilities.utils import (
    write_to_inventory, save_ip_to_config, save_switch_id, save_num_packets,
    save_num_bytes, save_api_base_url, save_monitor_interface, save_port_to_clients,
    save_port_to_router, save_model_name
)
from ovs_install.utilities.ansible_tasks import run_playbook
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
playbook_dir_path = f"{parent_dir}/ansible/playbooks"
inventory_path = f"{parent_dir}/ansible/inventory/inventory"
config_path = f"{parent_dir}/ansible/group_vars/all.yml"

def install_sniffer_util(lan_ip_address, api_base_url, monitor_interface, port_to_client, port_to_router, bridge_name, odl_switch_id, controller_ip):
    """
    Installs the traffic sniffer on a target device.

    Args:
        lan_ip_address (str): The IP address of the target device.
        api_base_url (str): The API base URL for sniffer.
        monitor_interface (str): The network interface to monitor.
        port_to_client (str): The port connected to clients.
        port_to_router (str): The port connected to the router.
        bridge_name (str): The name of the bridge on the target device.
        odl_switch_id (str): The ODL node ID of the switch (bridge).
        controller_ip (str): The IP address of the SDN controller managing the bridge.

    Returns:
        dict: A response dictionary indicating success or failure.
    """
    try:
        # Validate IP address
        validate_ipv4_address(lan_ip_address)
        device = get_object_or_404(Device, lan_ip_address=lan_ip_address,device_type='switch')

        inv_content = create_inv_data(lan_ip_address, device.username, device.password)
        inv_path = create_temp_inv(inv_content)

        # create config and env vars
        config_vars = {
            'switch_id': '0',
            'num_packets': 5,
            'num_bytes': 225,
            'ip_address': lan_ip_address,
            'api_base_url': api_base_url,
            'monitor_interface': monitor_interface,
            'port_to_clients': port_to_client,
            'port_to_router': port_to_router,
            'model_name': 'testing_sniffer',
            'bridge_name': bridge_name,
            'odl_node_id': odl_switch_id,
            'controller_ip': controller_ip,
        }

        # # Default settings for sniffer
        # save_switch_id('0', config_path)
        # save_num_packets(5, config_path)
        # save_num_bytes(225, config_path)

        # Save necessary configurations
        # write_to_inventory(lan_ip_address, device.username, device.password, inventory_path)
        # save_ip_to_config(lan_ip_address, config_path)

        # save_api_base_url(api_base_url, config_path)
        # save_monitor_interface(monitor_interface, config_path)
        # save_port_to_clients(port_to_client, config_path)
        # save_port_to_router(port_to_router, config_path)
        # save_model_name('testing_sniffer', config_path)

        # Run the Ansible playbook to install the sniffer
        result = run_playbook_with_extravars('install-sniffer-odl', playbook_dir_path, inv_path, config_vars, quiet=False)

        return {"status": "success", "message": "Successfully installed sniffer"}
    except ValidationError:
        return {"status": "error", "message": "Invalid IP address format."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def uninstall_sniffer_util(lan_ip_address):
    """
    Uninstalls the traffic sniffer from a target device.

    Args:
        lan_ip_address (str): The IP address of the target device.

    Returns:
        dict: A response dictionary indicating success or failure.
    """
    try:
        # Validate IP address
        validate_ipv4_address(lan_ip_address)
        device = get_object_or_404(Device, lan_ip_address=lan_ip_address, device_type='switch')

        inv_content = create_inv_data(lan_ip_address, device.username, device.password)
        inv_path = create_temp_inv(inv_content)

        # No extra vars needed for uninstall
        result = run_playbook_with_extravars('uninstall-sniffer-odl', playbook_dir_path, inv_path, extra_var={}, quiet=False)

        if result.get('status') == 'success':
            return {"status": "success", "message": "Successfully uninstalled sniffer"}
        else:
            return {"status": "error", "message": result.get('error', 'Unknown error during uninstall')}
    except ValidationError:
        return {"status": "error", "message": "Invalid IP address format."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def edit_sniffer_util(lan_ip_address, api_base_url, monitor_interface, port_to_client, port_to_router, bridge_name, odl_switch_id, controller_ip):
    """
    Updates the sniffer configuration on a target device by updating the .env file and restarting the service.

    Args:
        lan_ip_address (str): The IP address of the target device.
        api_base_url (str): The API base URL for sniffer.
        monitor_interface (str): The network interface to monitor.
        port_to_client (str): The port connected to clients.
        port_to_router (str): The port connected to the router.
        bridge_name (str): The name of the bridge on the target device.
        odl_switch_id (str): The ODL node ID of the switch (bridge).
        controller_ip (str): The IP address of the SDN controller managing the bridge.

    Returns:
        dict: A response dictionary indicating success or failure.
    """
    try:
        # Validate IP address
        validate_ipv4_address(lan_ip_address)
        device = get_object_or_404(Device, lan_ip_address=lan_ip_address, device_type='switch')

        inv_content = create_inv_data(lan_ip_address, device.username, device.password)
        inv_path = create_temp_inv(inv_content)

        config_vars = {
            'switch_id': '0',
            'num_packets': 5,
            'num_bytes': 225,
            'ip_address': lan_ip_address,
            'api_base_url': api_base_url,
            'monitor_interface': monitor_interface,
            'port_to_clients': port_to_client,
            'port_to_router': port_to_router,
            'model_name': 'testing_sniffer',
            'bridge_name': bridge_name,
            'odl_node_id': odl_switch_id,
            'controller_ip': controller_ip,
        }

        result = run_playbook_with_extravars('edit-sniffer-odl', playbook_dir_path, inv_path, config_vars, quiet=False)

        if result.get('status') == 'success':
            return {"status": "success", "message": "Successfully updated sniffer configuration"}
        else:
            return {"status": "error", "message": result.get('error', 'Unknown error during edit')}
    except ValidationError:
        return {"status": "error", "message": "Invalid IP address format."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
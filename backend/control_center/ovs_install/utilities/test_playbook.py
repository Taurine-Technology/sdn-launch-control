"""
Author: Keegan White
Maintainer: Keegan White
Contact: keeganthomaswhite@gmail.com
Created: Sep 4, 2023
Last Modified: Jan 9, 2024

Description:
This script serves as the main entry point for a series of operations related to Open vSwitch (OVS) configuration and management.
It automates tasks such as setting up connections to servers, updating inventory and configuration files, and running various
Ansible playbooks for network configuration and testing.

The script uses environment variables to manage sensitive information like IP addresses, usernames, and passwords. It demonstrates
the use of different utility functions and playbook execution to gather device details, show OVS bridges, and connect to OVS controllers.

Key functionalities:
- Loading environment variables and using them for server connections.
- Writing network device details to an inventory file for Ansible.
- Saving IP addresses, controller details, and bridge names to a configuration file.
- Running specific Ansible playbooks based on the test conditions.
"""

import os
import pathlib
from dotenv import load_dotenv
from .ansible_tasks import run_playbook
from .utils import write_to_inventory, save_ip_to_config, check_system_details, save_bridge_name_to_config, \
    save_controller_port_to_config, save_controller_ip_to_config
from .ovs_results_format import format_ovs_show, format_ovs_get_controller, format_ovs_show_bridge_command

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)


def main():
    # Load .env file
    load_dotenv()
    ip = os.getenv("ip")
    user = os.getenv("user")
    password = os.getenv("password")
    print(f"You are using IP address {ip}, Username {user} and Password {password} to connect to the target server.")

    abs_path = pathlib.Path(__file__).parent.resolve()
    test_playbook_name = 'ovs-show'
    test_server = "test-connection"
    playbook_dir_path = f"{parent_dir}/ansible/playbooks"
    inventory_path = f"{parent_dir}/ansible/inventory/inventory"
    config_path = f"{parent_dir}/ansible/group_vars/all.yml"

    # Write to variables to file
    write_to_inventory(ip, user, password, inventory_path)
    save_ip_to_config(ip, config_path)
    save_controller_port_to_config(6653, config_path)
    save_controller_ip_to_config('192.168.1.1', config_path)
    save_bridge_name_to_config('ovs_br', config_path)
    # Run initial playbooks
    # run_playbook(test_server, playbook_dir_path, inventory_path)
    if test_playbook_name == 'gather-device-details':
        results = run_playbook(test_playbook_name, playbook_dir_path, inventory_path)
        interfaces = check_system_details(results)

        print(interfaces)
    elif test_playbook_name == "ovs-show":
        results = run_playbook(test_playbook_name, playbook_dir_path, inventory_path)
        # print(results)
        print(format_ovs_show_bridge_command(results))
        print(format_ovs_show(results))
    elif test_playbook_name == "connect-to-controller":
        results = run_playbook(test_playbook_name, playbook_dir_path, inventory_path, False)
        format_ovs_show_bridge_command(results)
        format_ovs_get_controller(results)
    # test_playbook_name = 'ovs-switch-setup'
    # save_bridge_name_to_config('br0', config_path)
    # run_playbook(test_playbook_name, playbook_dir_path, inventory_path)


if __name__ == '__main__':
    main()

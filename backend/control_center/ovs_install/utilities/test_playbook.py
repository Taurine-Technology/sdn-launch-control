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
import logging

logger = logging.getLogger(__name__)

from utils.ansible_formtter import get_interfaces_from_results, get_filtered_interfaces
from utils.ansible_utils import run_playbook_with_extravars, create_temp_inv, create_inv_data

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)

def extract_ovs_port_map(playbook_result):
    """
    Extracts the ovs_port_map dictionary {interface_name: ofport_number}
    from the result of the 'get-ovs-port-numbers' playbook.

    Args:
        playbook_result (dict): The dictionary returned by run_playbook_with_extravars.
                                It's expected to have a 'status' and 'results' key.

    Returns:
        dict: The extracted ovs_port_map, or an empty dict if not found,
              if the playbook failed, or if the result format is unexpected.
    """
    ovs_map = {}
    if not isinstance(playbook_result, dict):
        logger.error("Invalid playbook_result format: Expected a dictionary.")
        return ovs_map # Return empty dict

    if playbook_result.get('status') != 'success':
        logger.warning("Playbook execution was not successful. Cannot extract port map.")
        # Optionally log playbook_result.get('error') if available
        return ovs_map # Return empty dict

    results_data = playbook_result.get('results')
    if not isinstance(results_data, dict):
        logger.warning("Playbook result missing 'results' dictionary.")
        return ovs_map # Return empty dict

    # --- Attempt 1: Extract from the debug task output (Preferred) ---
    try:
        # Ensure the task name matches exactly what's in the playbook's debug task
        debug_task_name = 'Show assembled OVS port map'
        debug_output = results_data.get(debug_task_name, {})
        if isinstance(debug_output, dict):
            potential_map = debug_output.get('ovs_port_map')
            if isinstance(potential_map, dict):
                 # Basic validation: keys are strings, values are integers
                if all(isinstance(k, str) and isinstance(v, int) for k, v in potential_map.items()):
                    logger.info(f"Successfully extracted ovs_port_map from debug task: {potential_map}")
                    return potential_map
                else:
                    logger.warning("Map found in debug task has invalid key/value types.")

    except Exception as e:
        logger.warning(f"Error accessing debug task output for ovs_port_map: {e}", exc_info=True)


    # --- Attempt 2: Extract from the set_fact task output (Fallback) ---
    try:
        # Ensure the task name matches exactly what's in the playbook's set_fact task
        set_fact_task_name = 'Assemble port map'
        set_fact_output = results_data.get(set_fact_task_name, {})
        if isinstance(set_fact_output, dict):
            loop_results = set_fact_output.get('results', [])
            if isinstance(loop_results, list) and loop_results:
                # The final map is in the 'ansible_facts' of the last item
                last_item = loop_results[-1]
                if isinstance(last_item, dict):
                    ansible_facts = last_item.get('ansible_facts', {})
                    if isinstance(ansible_facts, dict):
                        potential_map = ansible_facts.get('ovs_port_map')
                        if isinstance(potential_map, dict):
                            # Basic validation
                            if all(isinstance(k, str) and isinstance(v, int) for k, v in potential_map.items()):
                                logger.info(f"Successfully extracted ovs_port_map from set_fact task: {potential_map}")
                                return potential_map
                            else:
                                logger.warning("Map found in set_fact task has invalid key/value types.")

    except Exception as e:
        logger.warning(f"Error accessing set_fact task output for ovs_port_map: {e}", exc_info=True)


    # --- Attempt 3: Check if it exists at the top level of results (Less likely) ---
    # Sometimes facts might appear directly under results if not registered in a loop/task var
    try:
        potential_map = results_data.get('ovs_port_map')
        if isinstance(potential_map, dict):
             if all(isinstance(k, str) and isinstance(v, int) for k, v in potential_map.items()):
                logger.info(f"Successfully extracted ovs_port_map from top-level results: {potential_map}")
                return potential_map
             else:
                logger.warning("Map found in top-level results has invalid key/value types.")
    except Exception as e:
         logger.warning(f"Error accessing top-level results for ovs_port_map: {e}", exc_info=True)


    logger.warning("Could not find 'ovs_port_map' in any expected location within the playbook results.")
    return ovs_map # Return empty dict if not found

def main():
    # Load .env file
    load_dotenv()
    ip = os.getenv("ip")
    user = os.getenv("user")
    password = os.getenv("password")
    ports = ['enx1c61b4fefb88','enxac15a2d7d8e5']
    bridge_name = 'pi4br'
    print(f"You are using IP address {ip}, Username {user} and Password {password} to connect to the target server.")

    abs_path = pathlib.Path(__file__).parent.resolve()
    test_playbook_name = 'ovs-show'
    test_server = "test-connection"
    playbook_dir_path = f"{parent_dir}/ansible/playbooks"
    # inventory_path = f"{parent_dir}/ansible/inventory/inventory"
    # config_path = f"{parent_dir}/ansible/group_vars/all.yml"

    # Write to variables to file
    inv_content = create_inv_data(ip, user, password)
    inv_path = create_temp_inv(inv_content)

    # write_to_inventory(ip, user, password, inventory_path)
    # save_ip_to_config(ip, config_path)
    # save_controller_port_to_config(6653, config_path)
    # save_controller_ip_to_config('192.168.1.1', config_path)
    # save_bridge_name_to_config('ovs_br', config_path)

    get_ovs_nums_result = run_playbook_with_extravars(
        'get-ovs-port-numbers',
        playbook_dir_path,
        inv_path,
        {
            'interfaces': ports,
            'ip_address': ip,
            'bridge_name': bridge_name
        },
        quiet=True
    )
    ovs_port_map = extract_ovs_port_map(get_ovs_nums_result)
    print(f"Successfully extracted OVS port map: {ovs_port_map}")



    # Run initial playbooks
    # run_playbook(test_server, playbook_dir_path, inventory_path)
    # if test_playbook_name == 'gather-device-details':
    #     results = run_playbook(test_playbook_name, playbook_dir_path, inventory_path)
    #     interfaces = check_system_details(results)
    #
    #     print(interfaces)
    # elif test_playbook_name == "ovs-show":
    #     results = run_playbook(test_playbook_name, playbook_dir_path, inventory_path)
    #     # print(results)
    #     print(format_ovs_show_bridge_command(results))
    #     print(format_ovs_show(results))
    # elif test_playbook_name == "connect-to-controller":
    #     results = run_playbook(test_playbook_name, playbook_dir_path, inventory_path, False)
    #     format_ovs_show_bridge_command(results)
    #     format_ovs_get_controller(results)
    # test_playbook_name = 'ovs-switch-setup'
    # save_bridge_name_to_config('br0', config_path)
    # run_playbook(test_playbook_name, playbook_dir_path, inventory_path)


if __name__ == '__main__':
    main()

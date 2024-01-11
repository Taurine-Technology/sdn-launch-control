"""
Script: ovs_port_setup.py
Author: Keegan White
Maintainer: Keegan White
Created: Jan 9, 2024
Last Modified: Jan 9, 2024

Description:
Runs the ansible scripts and takes user input to select a bridge on the target device and add ports to it.

This script is part of ovs-management-toolbox and is used in main.py.
"""

from ..ansible_tasks import run_playbook
from ..utils import (save_bridge_name_to_config, save_interfaces_to_config, check_system_details)
from ..ovs_results_format import format_ovs_show

def setup_ovs_port(playbook_dir_path, inventory_path, interfaces, config_path=None):
    results = run_playbook('gather-device-details', playbook_dir_path, inventory_path)
    if interfaces == '':
        interfaces = check_system_details(results)
    results = run_playbook("ovs-show", playbook_dir_path, inventory_path)
    bridges = format_ovs_show(results)

    # Convert dictionary keys to a list
    bridge_names = list(bridges.keys())
    print(f"The target device has the following bridges:")
    for idx, choice in enumerate(bridge_names, 1):
        print(f"{idx}. {choice}")

    input_str = input("Please enter the number of the bridge you want to add ports to or enter exit to go to the main menu: ").strip()
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
    print(f"Select interfaces to use for bridge {bridge_name}:")
    for idx, choice in enumerate(interfaces, 1):
        print(f"{idx}. {choice}")
    while True:
        try:
            selected_indexes = input("Enter the interfaces you want to include in your OVS switch (comma-separated) or enter exit to go to the main menu: ").split(',')
            if selected_indexes[0] == 'exit':
                break
            interfaces = [interfaces[int(idx) - 1] for idx in selected_indexes]

            save_interfaces_to_config(interfaces, config_path)
            break
        except IndexError:
            print("Error: One or more of the interface numbers you provided are out of range. Please try again.")
        except ValueError:
            print(
                "Error: Invalid input detected. Please provide a comma-separated list of service numbers in base 10 "
                "format.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}. Please try again.")

    if selected_indexes[0] != 'exit':
        run_playbook('ovs-port-setup', playbook_dir_path, inventory_path)

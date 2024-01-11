from ..ansible_tasks import run_playbook
from ..utils import (save_bridge_name_to_config, save_interfaces_to_config, check_system_details)
from ..ovs_results_format import format_ovs_show, format_ovs_show_bridge_command


def ovs_show_bridge(playbook_dir_path, inventory_path, config_path=None):
    results = run_playbook("ovs-show", playbook_dir_path, inventory_path)
    bridges = format_ovs_show(results)

    # Convert dictionary keys to a list
    bridge_names = list(bridges.keys())
    print(f"The target device has the following bridges:")
    for idx, choice in enumerate(bridge_names, 1):
        print(f"{idx}. {choice}")

    input_str = input("Please enter the number of the bridge you want to view or enter exit to go to the main menu: ").strip()
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
    results = run_playbook('ovs-show', playbook_dir_path, inventory_path)
    bridge_results = format_ovs_show_bridge_command(results)
    print(f'{bridge_name} has the following configuration: ')
    print(f"OpenFlow version: {bridge_results['of_version']}")
    print(f"Datapath ID: {bridge_results['dpid']}")
    print(f"{bridge_results['n_tables']} tables")
    print(f"{bridge_results['n_buffers']} bufferss")




"""
Author: Keegan White
Maintainer: Keegan White
Contact: keeganthomaswhite@gmail.com
Created: Jan 11, 2024
Last Modified: Jan 11, 2024

Description:
This script is designed to automate and manage the execution of Ansible playbooks for network configuration and
management tasks. It leverages ansible_runner to run playbooks and captures their output for further processing.
The script is particularly tailored for operations involving Open vSwitch (OVS) configurations.

Functions:
1. my_status_handler: A callback function used by ansible_runner to handle status updates during playbook execution.
   It prints the current status of the playbook execution.
2. my_event_handler: A callback function used by ansible_runner to handle events during playbook execution.
   It processes and stores relevant data from playbook execution events.
3. run_playbook: Executes a specified Ansible playbook using ansible_runner, handling its output and errors.
   It returns a dictionary of results obtained from playbook execution.

These functions are integral to the application for executing and interpreting the results of Ansible playbooks,
especially in the context of network device configuration and Open vSwitch management.
"""

import ansible_runner
import sys

results = {}


def my_status_handler(data, runner_config):
    print('Status...')
    print(data['status'])


def my_event_handler(data):
    result = ''
    task = ''
    if data.get('event_data'):
        event_data = data['event_data']
        # print(event_data)
        if event_data.get('name'):
            event = event_data['name']
            print(event)
        if event_data.get('res') and event_data.get('task'):
            task = event_data['task']
            result = event_data['res']
    if task and result:
        if task != 'Gathering Facts':
            results[task] = result


def run_playbook(playbook_name, playbook_dir_path, inventory_path, quiet=True):
    playbook_path = f"{playbook_dir_path}/{playbook_name}.yml"
    try:
        r = ansible_runner.run(private_data_dir="./", playbook=playbook_path, inventory=inventory_path,
                               status_handler=my_status_handler, quiet=False, event_handler=my_event_handler)
        # Check if playbook run was successful
        if r.rc != 0:
            # print(results)
            # Specific error message for the missing ovs-vsctl command
            if playbook_name == 'ovs-show':
                msg = results['Get OVS Details']['msg']
                installation_err = "No such file or directory: b'ovs-vsctl'"
                if installation_err in msg:
                    print("It seems Open vSwitch (OVS) is not installed or isn't installed correctly "
                          "on the target machine, as the 'ovs-vsctl show' command failed.")
            else:
                print(f"Error running playbook: {playbook_name}")
                if hasattr(r, 'stdout'):
                    print("Details:", r.stdout)
                if hasattr(r, 'stderr'):
                    print("Error details:", r.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Unexpected error while running playbook: {playbook_name}")
        print(str(e))
        sys.exit(1)
    return results

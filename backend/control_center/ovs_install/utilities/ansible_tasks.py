"""
Author: Keegan White
Maintainer: Keegan White
Contact: keeganthomaswhite@gmail.com
Created: Jan 11, 2024
Last Modified: Jan 24, 2024

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
            # print(result)
            if 'msg' in result:
                msg = result['msg']
                if 'Failed to connect to the host via ssh' in msg:
                    results['failed'] = msg
    if task and result:
        if task != 'Gathering Facts':
            results[task] = result


def run_playbook(playbook_name, playbook_dir_path, inventory_path, quiet=True):
    playbook_path = f"{playbook_dir_path}/{playbook_name}.yml"
    try:
        r = ansible_runner.run(private_data_dir="./", playbook=playbook_path, inventory=inventory_path,
                               status_handler=my_status_handler, quiet=True, event_handler=my_event_handler)
        if r.rc != 0:
            print(f'*** RESULTS IN ERROR CHECK {results} ***')
            unreachable_err = 'Failed to connect to the host via ssh:'
            if results:
                # if results.get('Get OVS Details'):
                #     msg = results['Get OVS Details']['msg']
                #     installation_err = "No such file or directory: b'ovs-vsctl'"
                #     if installation_err in msg:
                #         error_explanation = "It seems Open vSwitch (OVS) is not installed or isn't installed correctly on the target machine, as the 'ovs-vsctl show' command failed."
                #         print("ovs-vsctl show command failed.")
                #         return {'status': 'failed', 'error': error_explanation}
                # SSH error
                if results.get('failed'):
                    if results['failed'].get(unreachable_err):
                        return {'status': 'failed', 'error': results['failed']}
                # Apt update error
                elif results.get('Install required packages'):
                    print('made it to apt get install')
                    print(results['Install required packages'])
                    results_apt = results['Install required packages']
                    print(results_apt)
                    #  'stderr': 'E: Could not get lock /var/lib/dpkg/lock-frontend
                    if results_apt.get('stderr'):
                        results_err = results_apt['stderr']
                        print('results error found')
                        print(results_err)

                        if 'Could not get lock' in results_err:
                            return {'status': 'failed', 'error': 'Cannot get lock while running apt install. Try restarting your device and trying again.'}
                        else:
                            return {'status': 'failed', 'error': results_err}
                    else:
                        return {'status': 'failed', 'error': 'unknown error.'}
                else:
                    return {'status': 'failed', 'error': 'unknown error.'}
            else:
                return {'status': 'failed', 'error': 'unknown error.'}

        return {'status': 'success', 'results': results}

    except Exception as e:
        print(f'***___RETURNING ERROR {e}___***')
        print(results)
        return {'status': 'failed', 'error': str(e)}

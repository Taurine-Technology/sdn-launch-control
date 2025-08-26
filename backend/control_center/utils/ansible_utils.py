# File: ansible_utils.py
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
import tempfile

results = {}

def create_temp_inv(inventory_content):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_inv:

        temp_inv.write(inventory_content)
        temp_inv.flush()  # Ensure content is written to disk.
        inv_path = temp_inv.name
        return inv_path


def create_inv_data(ip, user, password,) :
    content = (f"[localserver]\n "
               f"{ip} ansible_user='{user}' ansible_password='{password}' "
               f"ansible_ssh_common_args='-o StrictHostKeyChecking=no' ansible_become_pass='{password}' "
               f"ansible_become_method=sudo ansible_become_timeout=30\n")
    return content

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


def run_playbook_with_env(playbook_name, playbook_dir_path, inventory_path, env_dict, quiet=True):
    playbook_path = f"{playbook_dir_path}/{playbook_name}.yml"
    try:
        r = ansible_runner.run(private_data_dir="./", envvars=env_dict, playbook=playbook_path, inventory=inventory_path,
                               status_handler=my_status_handler, quiet=quiet, event_handler=my_event_handler)
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
                    if isinstance(results['failed'], str):
                        return {'status': 'failed', 'error': results['failed']}
                    elif results['failed'].get(unreachable_err):
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
                return {'status': 'failed', 'error': 'Incorrect username/password combination.'}

        return {'status': 'success', 'results': results}

    except Exception as e:
        print(f'***___RETURNING ERROR {e}___***')
        print(results)
        return {'status': 'failed', 'error': str(e)}


def run_playbook_with_extravars(playbook_name, playbook_dir_path, inventory_path, extra_var=None, quiet=True):
    global results
    if extra_var is None:
        extra_var = {}
    
    # Clear results from previous runs
    results = {}
    
    playbook_path = f"{playbook_dir_path}/{playbook_name}.yml"
    try:
        r = ansible_runner.run(
            private_data_dir="./",
            extravars=extra_var,
            playbook=playbook_path,
            inventory=inventory_path,
            status_handler=my_status_handler,
            quiet=False,
            event_handler=my_event_handler
        )
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
                    if isinstance(results['failed'], str):
                        return {'status': 'failed', 'error': results['failed']}
                    elif results['failed'].get(unreachable_err):
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
                            return {'status': 'failed',
                                    'error': 'Cannot get lock while running apt install. Try restarting your device and trying again.'}
                        else:
                            return {'status': 'failed', 'error': results_err}
                    else:
                        return {'status': 'failed', 'error': 'unknown error.'}
                else:
                    return {'status': 'failed', 'error': 'unknown error.'}
            else:
                return {'status': 'failed', 'error': 'Incorrect username/password combination.'}

        return {'status': 'success', 'results': results}

    except Exception as e:
        print(f'***___RETURNING ERROR {e}___***')
        print(results)
        return {'status': 'failed', 'error': str(e)}

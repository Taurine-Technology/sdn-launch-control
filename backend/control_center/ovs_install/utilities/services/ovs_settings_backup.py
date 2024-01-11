"""
Author: Keegan White
Maintainer: Keegan White
Contact: keeganthomaswhite@gmail.com
Created: Jan 9, 2024
Last Modified: Jan 9, 2024

Description:
This script is part of ovs-management-toolbox and is responsible for backing up Open vSwitch (OVS) settings to a yaml file.
It prompts the user for confirmation to proceed with the backup, gathers device details and OVS bridge information,
and then performs the backup operation.

This module is a part of the service 'ovs-settings-backup' in the main(.py) application.
"""
from src.ansible_tasks import run_playbook
from src.ovs_results_format import format_ovs_show
from src.utils import check_system_details, update_devices

def ovs_settings_backup(playbook_dir_path, inventory_path, user, password, ip):
    continue_backup = input("The backup requires OVS to be installed on your target device else it will fail. Have you installed OVS on the target device? (y/n) ").strip().lower()

    if continue_backup == 'y':
        print("Backing up device...")
        results = run_playbook('gather-device-details', playbook_dir_path, inventory_path)
        interfaces = check_system_details(results)
        results = run_playbook("ovs-show", playbook_dir_path, inventory_path)
        bridges = format_ovs_show(results)

        device_name = input("Please provide a unique name to use for your device: ").strip()
        update_devices(device_name, bridges, user, password, ip, 'backup.yml')
    else:
        print("Exiting backup process...")

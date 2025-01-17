# File: ovs_settings_backup.py
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
This script is part of ovs-management-toolbox and is responsible for backing up Open vSwitch (OVS) settings to a yaml file.
It prompts the user for confirmation to proceed with the backup, gathers device details and OVS bridge information,
and then performs the backup operation.
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

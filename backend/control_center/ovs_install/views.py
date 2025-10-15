# File: views.py
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

import os
import time
from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework.response import Response
from .utilities.ansible_tasks import run_playbook
from general.models import Device, Port
from .utilities.utils import check_system_details
from utils.ansible_formtter import get_interface_speeds_from_results
from django.shortcuts import get_object_or_404
from utils.ansible_utils import run_playbook_with_extravars, create_temp_inv, create_inv_data
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError
import logging
from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .utilities.utils import write_to_inventory, save_ip_to_config, save_api_url_to_config, save_pi_bool
from time import sleep

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
logger = logging.getLogger(__name__)
install_ovs = "install-ovs"
playbook_dir_path = f"{parent_dir}/ansible/playbooks"
inventory_path = f"{parent_dir}/ansible/inventory/inventory"
config_path = f"{parent_dir}/ansible/group_vars/all.yml"
get_ports = "get-ports"
install_system_monitor = "install-stats-monitor"


class InstallOvsView(APIView):

    def post(self, request):
        """
        Handle POST requests to install Open vSwitch on a remote device and record its ports.
        
        This endpoint validates the provided LAN IP address, runs Ansible playbooks to install OVS and a system monitor on the target device, discovers network interfaces and their speeds, and persists a Device record (creating Port records for discovered interfaces when a new device is created). It also updates an existing device to mark OVS as enabled if necessary and logs execution duration and discovered details.
        
        Returns:
            Response: A Django REST framework Response whose JSON body contains:
                - "status": "success" or "error"
                - "message": a human-readable message
            Uses HTTP 200 for success and HTTP 400 for errors. If the IP address is invalid, the response is HTTP 400 with message "Invalid IP address format." On other failures, the response is HTTP 400 with the exception message.
        """
        start_time = time.perf_counter()
        try:

            data = request.data
            validate_ipv4_address(data.get('lan_ip_address'))
            is_pi = data.get('is_pi')
            requested_device_type = data.get('device_type')
            requested_name = data.get('name')
            requested_username = data.get('username')
            requested_password = data.get('password')
            requested_os_type = data.get('os_type')
            # save_pi_bool(is_pi, config_path)
            lan_ip_address = data.get('lan_ip_address')
            inv_content = create_inv_data(lan_ip_address, data.get('username'), data.get('password'))
            inv_path = create_temp_inv(inv_content)


            # write_to_inventory(lan_ip_address, data.get('username'), data.get('password'), inventory_path)

            # save_ip_to_config(lan_ip_address, config_path)
            # result_install = run_playbook(install_ovs, playbook_dir_path, inventory_path)
            result_install = run_playbook_with_extravars(
                install_ovs,
                playbook_dir_path,
                inv_path,
                {
                    'is_pi': is_pi,
                    'ip_address': lan_ip_address
                }
            )


            if result_install['status'] == 'failed':
                logger.error('install-ovs failed')
                return Response({"status": "error", "message": result_install['error']}, status=status.HTTP_400_BAD_REQUEST)

            # save_api_url_to_config(data.get('api_url'), config_path)
            api_url = data.get('api_url')
            result_install_monitor = run_playbook_with_extravars(
                install_system_monitor,
                playbook_dir_path,
                inv_path,
                {
                    'is_pi': is_pi,
                    'api_url': api_url,
                    'ip_address': lan_ip_address
                }
            )
            if result_install_monitor['status'] == 'failed':
                logger.error('install-system_monitor failed')
                return Response({"status": "error", "message": result_install_monitor['error']}, status=status.HTTP_400_BAD_REQUEST)
           
            result = run_playbook_with_extravars(get_ports, playbook_dir_path, inv_path)
            interfaces = check_system_details(result)
            interface_speeds = get_interface_speeds_from_results(result.get('results', {}))
            logger.info(f'Interfaces discovered: {interfaces}')
            logger.info(f'Interface speeds: {interface_speeds}')
            if interfaces is not None:
                num_ports = len(interfaces)
            else:
                num_ports = 0

            device, created = Device.objects.get_or_create(
                lan_ip_address=lan_ip_address,
                device_type=requested_device_type,
                defaults={
                    'name': requested_name,
                    'username': requested_username,
                    'password': requested_password,
                    'os_type': requested_os_type,
                    'ovs_enabled': True,  # Set for new devices
                    'ovs_version': '2.17.7',
                    'openflow_version': '1.3',
                    'num_ports': num_ports
                }
            )

            # Update ovs_enabled if device already exists and it's false
            if not created and not device.ovs_enabled:
                device.ovs_enabled = True
                device.save(update_fields=['ovs_enabled'])
            if created:
                if interfaces is not None:
                    logger.info(f'Creating {len(interfaces)} ports for device {device.name}')
                    for interface in interfaces:
                        port, created_ports = Port.objects.get_or_create(
                            name=interface,
                            device=device,
                            defaults={
                                'device': device,
                                'link_speed': interface_speeds.get(interface)
                            }
                        )

            message = "OVS Installed." if created else "OVS already installed."
            end_time = time.perf_counter()
            duration = end_time - start_time

            logger.info(
                f"InstallOvsView execution time (success): {duration:.4f} seconds"
            )

            return Response({"status": "success", "message": message}, status=status.HTTP_200_OK)
        except ValidationError:
            return Response({"status": "error", "message": "Invalid IP address format."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'Error in InstallOvsView: {str(e)}', exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

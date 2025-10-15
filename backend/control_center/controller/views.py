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

from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework.response import Response
from ovs_install.utilities.ansible_tasks import run_playbook
from general.models import Device, Port, Controller
from ovs_install.utilities.utils import check_system_details
from utils.ansible_formtter import get_interface_speeds_from_results
from django.shortcuts import get_object_or_404
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError
import logging
from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from utils.ansible_utils import run_playbook_with_extravars, create_temp_inv, create_inv_data


from ovs_install.utilities.utils import write_to_inventory, save_ip_to_config

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
logger = logging.getLogger(__name__)
install_onos = "install-onos"
install_faucet = "install-faucet"
install_odl = "install-odl"
playbook_dir_path = f"{parent_dir}/ansible/playbooks"
inventory_path = f"{parent_dir}/ansible/inventory/inventory"
config_path = f"{parent_dir}/ansible/group_vars/all.yml"
get_ports = "get-ports"


class InstallControllerView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, controller_type):
        try:
            data = request.data
            validate_ipv4_address(data.get('lan_ip_address'))
            lan_ip_address = data.get('lan_ip_address')
            # write_to_inventory(lan_ip_address, data.get('username'), data.get('password'), inventory_path)
            inv_content = create_inv_data(lan_ip_address,  data.get('username'),data.get('password'))
            inv_path = create_temp_inv(inv_content)
            # save_ip_to_config(lan_ip_address, config_path)

            if controller_type == 'onos':
                result_install = run_playbook_with_extravars(
                    install_onos,
                    playbook_dir_path,
                    inv_path, 
                    {
                    'ip_address': lan_ip_address,
                    }
                )
            # elif controller_type == 'faucet':
            #     result_install = run_playbook(install_faucet, playbook_dir_path, inventory_path)
            elif controller_type == 'odl':
                result_install = run_playbook_with_extravars(install_odl, playbook_dir_path, inv_path,{'ip_address': lan_ip_address,}, quiet=False)
            else:
                return Response({"status": "error", "message": "Invalid controller type"}, status=status.HTTP_400_BAD_REQUEST)

            if result_install['status'] == 'failed':
                logger.error(f'Controller installation failed: {result_install}')
                return Response({"status": "error", "message": result_install['error']}, status=status.HTTP_400_BAD_REQUEST)
            logger.info(f'Installing {controller_type} on device')
            result = run_playbook(get_ports, playbook_dir_path, inv_path)
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
                device_type=data.get('device_type'),
                defaults={
                    'name': data.get('name'),

                    'username': data.get('username'),
                    'password': data.get('password'),
                    'os_type': data.get('os_type'),
                    'ovs_enabled': False,
                    'num_ports': num_ports
                }
            )
            if created:
                if interfaces is not None:
                    logger.info(f'Creating {len(interfaces)} ports for device {device.name}')
                    for interface in interfaces:
                        port, created_ports = Port.objects.get_or_create(
                            name=interface,
                            device=device,
                            defaults={
                                'link_speed': interface_speeds.get(interface)
                            }
                        )
            controller = Controller.objects.get_or_create(
                type=controller_type,
                device=device,
            )
            message = "Controller Installed." if created else "Controller already installed."
            return Response({"status": "success", "message": message}, status=status.HTTP_200_OK)
        except ValidationError:
            return Response({"status": "error", "message": "Invalid IP address format."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'Error in InstallControllerView: {str(e)}', exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

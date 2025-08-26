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

from utils.ansible_formtter import get_interfaces_from_results, get_filtered_interfaces, extract_ovs_port_map
from utils.ansible_utils import run_playbook_with_extravars, create_temp_inv, create_inv_data
from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework.response import Response
from django.db import transaction
from ovs_install.utilities.services.ovs_port_setup import setup_ovs_port
from ovs_install.utilities.ansible_tasks import run_playbook
from ovs_install.utilities.utils import check_system_details
from ovs_install.utilities.ovs_results_format import format_ovs_show, format_ovs_show_bridge_command
from general.models import Device, Bridge, Port
from django.shortcuts import get_object_or_404
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError
import logging
from general.serializers import BridgeSerializer, PortSerializer
from ovs_install.utilities.utils import write_to_inventory, save_ip_to_config, save_bridge_name_to_config, \
    save_interfaces_to_config, save_controller_port_to_config, save_controller_ip_to_config
from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from general.models import Controller
from software_plugin.models import SnifferInstallationConfig, PluginInstallation
from utils.install_plugin import uninstall_sniffer_util


script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
logger = logging.getLogger(__name__)
install_ovs = "install-ovs"
get_ports = "get-ports"
ovs_show = 'ovs-show'
playbook_dir_path = f"{parent_dir}/ansible/playbooks"
inventory_path = f"{parent_dir}/ansible/inventory/inventory"
config_path = f"{parent_dir}/ansible/group_vars/all.yml"
install_qos_monitor = "run-ovs-qos-monitor"


class GetDevicePorts(APIView):
    def get(self, request, lan_ip_address):
        """
        Returns all ports (assigned and unassigned) without the bridge ports
        :param request: type of request
        :param lan_ip_address: ip address of device
        :return: interfaces on the device without the bridges
        """
        try:
            validate_ipv4_address(lan_ip_address)
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address,device_type="switch")


            result = run_playbook(get_ports, playbook_dir_path, inventory_path)  # Ensure these variables are defined
            interfaces = check_system_details(result)
            print(f'Interfaces {interfaces}')

            existing_ports = device.ports.all()  # Get all ports currently associated with the device
            existing_port_names = [port.name for port in existing_ports]

            new_ports = []
            for interface_name in interfaces:
                if interface_name not in existing_port_names:
                    # Interface not in DB, create and add it
                    new_port = Port(device=device, name=interface_name)
                    new_port.save()
                    new_ports.append(new_port.name)
            if new_ports:
                print(f'New ports added: {new_ports}')
            # remove bridges from port list returned
            bridges = device.bridges.all()
            bridge_names = [bridge.name for bridge in bridges]
            ports = device.ports.all()
            # Filter ports that do not match any bridge names
            all_ports = [port for port in ports if port.name not in bridge_names and port.name != 'ovs-system']
            # Extracting interface names for the response
            all_interface_names = [port.name for port in all_ports]
            print(f'All ports: {all_ports}')
            return Response({"status": "success", "interfaces": all_interface_names}, status=status.HTTP_200_OK)

        except ValidationError:
            return Response({"status": "error", "message": "Invalid IP address format."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(e, exc_info=True)
            print('ERROR HERE')
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetUnassignedDevicePorts(APIView):
    def get(self, request, lan_ip_address):
        """
        Returns unassigned ports for a device without the bridge ports
        :param request: type of request
        :param lan_ip_address: ip address of device
        :return: interfaces on the device without the bridges
        """
        try:
            validate_ipv4_address(lan_ip_address)
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address,device_type='switch')

            # Assuming run_playbook and check_system_details are implemented and return interface names
            # result = run_playbook(get_ports, playbook_dir_path, inventory_path)  # Ensure these variables are defined
            inv_content = create_inv_data(lan_ip_address, device.username, device.password)
            inv_path = create_temp_inv(inv_content)
            result_ip_link = run_playbook_with_extravars('get-ports-ip-link', playbook_dir_path, inv_path)
            # print(result_ip_link)

            interfaces = get_filtered_interfaces(result_ip_link)

            existing_ports = device.ports.all()  # Get all ports currently associated with the device
            existing_port_names = [port.name for port in existing_ports]

            new_ports = []
            if interfaces:
                for interface_name in interfaces:
                    if interface_name not in existing_port_names:
                        # Interface not in DB, create and add it
                        new_port = Port(device=device, name=interface_name)
                        new_port.save()
                        new_ports.append(new_port.name)
                # if new_ports:
                #     print(f'New ports added: {new_ports}')

            # get unassociated ports and return them:
            bridges = device.bridges.all()
            bridge_names = [bridge.name for bridge in bridges]
            ports = device.ports.all()
            # Filter ports that are not assigned to any bridge and whose names do not match any bridge names
            unassigned_ports = [port for port in ports if
                                port.bridge is None and port.name not in bridge_names and port.name != 'ovs-system']
            # Extracting interface names for the response
            unassigned_interface_names = [port.name for port in unassigned_ports]
            # print(f'Unassigned ports: {unassigned_ports}')
            return Response({"status": "success", "interfaces": unassigned_interface_names}, status=status.HTTP_200_OK)

        except ValidationError:
            return Response({"status": "error", "message": "Invalid IP address format."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(e, exc_info=True)
            print('ERROR HERE')
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssignPorts(APIView):
    def post(self, request):
        try:
            data = request.data
            print(data)
            ports = data.get('ports')
        except Exception as e:
            print(e)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GetBridgePortsView(APIView):
    """
    Retrieve ports associated with a specific bridge on a device,
    including their OVS port numbers.
    """

    def get(self, request, lan_ip_address, bridge_name):
        try:
            validate_ipv4_address(lan_ip_address)
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address,device_type='switch')
            bridge = get_object_or_404(Bridge, device=device, name=bridge_name)

            # Fetch ports associated with this bridge that HAVE an OVS port number
            ports_qs = Port.objects.filter(
                device=device,
                bridge=bridge,
                ovs_port_number__isnull=False # Only include ports with an assigned OVS number
            ).order_by('ovs_port_number') # order by number

            serializer = PortSerializer(ports_qs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ValidationError as e:
             logger.warning(f"Validation error fetching bridge ports: {e}")
             return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Device.DoesNotExist:
             logger.warning(f"Device not found: {lan_ip_address}")
             return Response({'status': 'error', 'message': 'Device not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Bridge.DoesNotExist:
             logger.warning(f"Bridge '{bridge_name}' not found on device {lan_ip_address}.")
             return Response({'status': 'error', 'message': 'Bridge not found on this device.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
             logger.error(f"Error fetching ports for bridge {bridge_name} on {lan_ip_address}: {e}", exc_info=True)
             return Response({'status': 'error', 'message': 'An internal server error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetDeviceBridges(APIView):
    """
    Use this to get bridge ports for a device and sync the DB with the device.
    """

    def get(self, request, lan_ip_address):
        try:
            # Validate the IP address
            validate_ipv4_address(lan_ip_address)

            # Get the device or raise 404
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address,device_type='switch')
            inv_content = create_inv_data(lan_ip_address, device.username, device.password)
            inv_path = create_temp_inv(inv_content)
            # Sync the device with the inventory and run the playbook

            # write_to_inventory(lan_ip_address, device.username, device.password, inventory_path)
            print('*** running OVS show ***')
            result = run_playbook_with_extravars(ovs_show, playbook_dir_path, inv_path)

            if result['status'] == 'failed':
                return Response(
                    {'status': 'error', 'message': result['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Format the result into bridges
            bridges = format_ovs_show(result['results'])
            new_ports = []
            print('we found', bridges)
            for bridge in bridges:
                # save_bridge_name_to_config(bridge, config_path)
                get_bridge_details = run_playbook_with_extravars(
                    'ovs-bridge-details', playbook_dir_path, inv_path, {
                    'bridge_name': bridge
                    }
                )
                # Get details for the current bridge
                # get_bridge_details = run_playbook('ovs-bridge-details', playbook_dir_path, inventory_path)
                bridge_details = format_ovs_show_bridge_command(get_bridge_details['results'])
                dpid = bridge_details['dpid']

                # Handle controller if it exists
                if bridges[bridge].get('Controller'):
                    controller = bridges[bridge]['Controller'][0]
                    controller_details = controller.split(':')
                    controller_ip = controller_details[1]
                    controller_port = controller_details[2]
                    controller_name = f'Auto Sync: {controller_ip}'
                    # Get or create the controller device
                    controller_device_db, created = Device.objects.update_or_create(
                        lan_ip_address=controller_ip,
                        device_type='controller',
                        defaults={
                            'os_type' : 'unknown',
                            'name' : controller_name,
                        }
                    )

                    # Get or create the controller
                    if not created:
                        controller_db, _ = Controller.objects.get_or_create(
                            device=controller_device_db,
                            defaults={
                                'type': 'unknown',
                                'port_num': controller_port,
                            }
                        )
                    else:
                        controller_db = Controller.objects.create(
                            type='unknown',
                            device=controller_device_db,
                            port_num=controller_port,
                        )

                    # Link the controller to the current device
                    controller_db.switches.add(device)
                else:
                    controller_db = None

                # Update or create the bridge
                db_bridge, created = Bridge.objects.update_or_create(
                    device=device,
                    name=bridge,
                    defaults={
                        'dpid': dpid,
                        'controller': controller_db,
                    }
                )

                # Handle ports
                if bridges[bridge].get('Ports'):
                    ports = bridges[bridge]['Ports']
                    for interface_name in ports:
                        port, created = Port.objects.update_or_create(
                            device=device, name=interface_name,
                            defaults=
                            {
                                'bridge': db_bridge
                            }
                        )

            return Response({'status': 'success', 'bridges': bridges}, status=status.HTTP_200_OK)

        except ValidationError as e:
            logger.error(f'Validation error: {str(e)}', exc_info=True)
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'Error in GetDeviceBridges: {str(e)}', exc_info=True)
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetDeviceBridgeDpid(APIView):
    def get(self, request):
        try:
            data = request.data
            lan_ip_address = data.get('lan_ip_address')
            validate_ipv4_address(lan_ip_address)

            result = run_playbook(ovs_show, playbook_dir_path, inventory_path)
            if result['status'] == 'failed':
                return Response({'status': 'error', 'message': result['error']},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            bridges = format_ovs_show(result)
            return Response({'status': 'success', 'bridges': bridges}, status=status.HTTP_200_OK)
        except ValidationError as e:
            logger.error(f'Validation error: {str(e)}', exc_info=True)
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'Error in GetDeviceBridges: {str(e)}', exc_info=True)
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EditBridge(APIView):
    @transaction.atomic # Ensure atomicity for the edit operation
    def put(self, request):
        """
        Edit an existing bridge: ports, controller, api_url.
        Manages OVS port number assignment/clearing.
        """
        try:
            data = request.data
            lan_ip_address = data.get('lan_ip_address')
            validate_ipv4_address(lan_ip_address)
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address,device_type='switch')

            bridge_name = data.get('name')
            if not bridge_name:
                 return Response({'status': 'error', 'message': 'Bridge name is required for editing.'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Get the bridge instance within the transaction
            original_bridge = get_object_or_404(Bridge, name=bridge_name, device=device)

            # --- Prepare Ansible ---
            inv_content = create_inv_data(lan_ip_address, device.username, device.password)
            inv_path = create_temp_inv(inv_content)

            # Flags to track changes
            bridge_needs_save = False # For changes directly on the Bridge model (api_url, controller)
            ports_changed = False
            api_url_changed = False
            controller_changed = False

            # --- 1. Update api_url if provided ---
            if 'api_url' in data:
                new_api_url = data.get('api_url') # Can be None or empty string
                if original_bridge.api_url != new_api_url:
                     logger.info(f"Updating api_url for bridge {bridge_name} to '{new_api_url}'")
                     original_bridge.api_url = new_api_url
                     api_url_changed = True
                     bridge_needs_save = True

            # --- 2. Handle Port Changes ---
            ports_to_add = []
            ports_to_remove = []
            ovs_port_map = {} # Initialize map for OVS numbers

            if 'ports' in data:
                new_ports_names = data.get('ports', []) # List of desired port names
                # Get current port names directly associated with the bridge in DB
                original_port_names = list(original_bridge.ports.values_list('name', flat=True))

                new_ports_set = set(new_ports_names)
                original_ports_set = set(original_port_names)

                ports_to_add = list(new_ports_set - original_ports_set)
                ports_to_remove = list(original_ports_set - new_ports_set)

                if ports_to_add or ports_to_remove:
                    ports_changed = True

                # --- 2a. Remove Ports from Device and Update DB ---
                if ports_to_remove:
                    logger.info(f"Removing ports {ports_to_remove} from bridge {bridge_name}")
                    delete_ports_playbook = 'ovs-delete-ports' # Assumes this playbook exists
                    delete_ports_vars = {
                        'interfaces': ports_to_remove,
                        'ip_address': lan_ip_address,
                        'bridge_name': bridge_name
                    }
                    delete_interfaces_result = run_playbook_with_extravars(
                        delete_ports_playbook, playbook_dir_path, inv_path, delete_ports_vars
                    )
                    if delete_interfaces_result.get('status') == 'failed':
                        error_detail = delete_interfaces_result.get('error', 'Unknown Ansible error')
                        logger.error(f"Playbook '{delete_ports_playbook}' failed for {bridge_name}: {error_detail}")
                        raise Exception(f"Failed to remove interfaces from bridge via Ansible: {error_detail}")

                    # Update DB for removed ports
                    ports_qs = Port.objects.filter(name__in=ports_to_remove, device=device, bridge=original_bridge)
                    updated_count = ports_qs.update(bridge=None, ovs_port_number=None)
                    logger.info(f"Unassigned {updated_count} ports from bridge {bridge_name} in DB.")


                # --- 2b. Add Ports to Device ---
                if ports_to_add:
                    logger.info(f"Adding ports {ports_to_add} to bridge {bridge_name}")
                    add_ports_playbook = 'ovs-port-setup'
                    add_ports_vars = {
                        'interfaces': ports_to_add,
                        'ip_address': lan_ip_address,
                        'bridge_name': bridge_name
                    }
                    add_interfaces_result = run_playbook_with_extravars(
                        add_ports_playbook, playbook_dir_path, inv_path, add_ports_vars
                    )
                    if add_interfaces_result.get('status') == 'failed':
                        error_detail = add_interfaces_result.get('error', 'Unknown Ansible error')
                        logger.error(f"Playbook '{add_ports_playbook}' failed for {bridge_name}: {error_detail}")
                        raise Exception(f"Failed to add interfaces to bridge via Ansible: {error_detail}")

                # --- 2c. Get OVS Port Numbers for *Current* Bridge State ---
                # If ports were added or removed, we need to refresh the OVS numbers
                if ports_changed:
                    # Determine the final list of ports expected on the bridge after adds/removes
                    final_port_names = list((original_ports_set - set(ports_to_remove)) | set(ports_to_add))

                    if final_port_names: # Only run if bridge is expected to have ports
                        get_ovs_nums_playbook = 'get-ovs-port-numbers'
                        get_ovs_nums_vars = {
                            'bridge_name': bridge_name,
                            'interfaces': final_port_names,
                            'ip_address': lan_ip_address,
                        }
                        logger.info(f"Running playbook '{get_ovs_nums_playbook}' for bridge {bridge_name} (ports: {final_port_names})")
                        get_ovs_nums_result = run_playbook_with_extravars(
                            get_ovs_nums_playbook, playbook_dir_path, inv_path, get_ovs_nums_vars
                        )

                        ovs_port_map = extract_ovs_port_map(get_ovs_nums_result) # Use the formatter

                        if not ovs_port_map:
                             if get_ovs_nums_result.get('status') == 'failed':
                                 error_detail = get_ovs_nums_result.get('error', 'Extraction failed')
                                 logger.error(f"Playbook '{get_ovs_nums_playbook}' failed during edit for {bridge_name}: {error_detail}")
                                 raise Exception(f"Failed to execute OVS port number retrieval during edit: {error_detail}")
                             else:
                                 logger.error(f"Failed to parse OVS port numbers during edit for bridge {bridge_name}.")
                                 raise Exception(f"Critical error: Could not determine OVS port numbers for bridge {bridge_name} during edit.")
                    else:
                        logger.info(f"Bridge {bridge_name} has no ports after edit, skipping OVS number retrieval.")
                        ovs_port_map = {} # Ensure it's empty

                # --- 2d. Update DB for Added Ports (and potentially existing ones) ---
                for port_name in ports_to_add:
                    port_obj, created = Port.objects.get_or_create(name=port_name, device=device)
                    port_obj.bridge = original_bridge
                    port_obj.ovs_port_number = ovs_port_map.get(port_name) # Assign number
                    port_obj.save(update_fields=['bridge', 'ovs_port_number'])
                    if created:
                        logger.info(f"Created new port entry for {port_name} on device {device.name} during edit.")
                    if port_obj.ovs_port_number is None:
                        logger.warning(f"Port {port_name} added to bridge {bridge_name} during edit, but OVS port number was not found/assigned.")

                # Optional: Refresh OVS numbers for ports that remained on the bridge
                if ports_changed: # Only if adds/removes happened
                    ports_that_remained = original_ports_set - set(ports_to_remove)
                    for port_name in ports_that_remained:
                         port_obj = Port.objects.get(name=port_name, device=device, bridge=original_bridge)
                         new_num = ovs_port_map.get(port_name)
                         if port_obj.ovs_port_number != new_num:
                              logger.info(f"Updating OVS port number for existing port {port_name} on bridge {bridge_name} to {new_num}")
                              port_obj.ovs_port_number = new_num
                              port_obj.save(update_fields=['ovs_port_number'])


            # --- 3. Handle Controller Changes ---
            new_controller = None # Target controller object
            if 'controller' in data:
                controller_data = data.get('controller')
                current_controller = original_bridge.controller # Controller currently on the bridge

                if controller_data and controller_data.get('lan_ip_address'):
                    # Assigning/Changing controller
                    controller_ip = controller_data.get('lan_ip_address')
                    try:
                        controller_device = get_object_or_404(Device, lan_ip_address=controller_ip,device_type="controller")
                        new_controller = get_object_or_404(Controller, device=controller_device)
                    except (Device.DoesNotExist, Controller.DoesNotExist) as e:
                         raise ValidationError(f"Specified controller (IP: {controller_ip}) not found.") from e

                    if current_controller != new_controller:
                        controller_changed = True
                elif controller_data is None and current_controller is not None:
                    # Removing controller (setting to null)
                    controller_changed = True
                    new_controller = None # Target is None
                # Else: No change specified or invalid data, ignore

            if controller_changed:
                bridge_needs_save = True
                current_controller = original_bridge.controller # Get again inside transaction

                # --- 3a. Remove Old Controller from Device ---
                if current_controller:
                    logger.info(f"Removing bridge {bridge_name} from old controller {current_controller.device.lan_ip_address}")
                    remove_controller_playbook = 'remove-controller'
                    remove_controller_vars = {
                         'ip_address': lan_ip_address,
                         'bridge_name': bridge_name
                    }
                    delete_controller_result = run_playbook_with_extravars(
                        remove_controller_playbook, playbook_dir_path, inv_path, remove_controller_vars
                    )
                    if delete_controller_result.get('status') == 'failed':
                        error_detail = delete_controller_result.get('error', 'Unknown Ansible error')
                        logger.error(f"Playbook '{remove_controller_playbook}' failed for {bridge_name}: {error_detail}")
                        raise Exception(f'Failed to remove old controller from bridge via Ansible: {error_detail}')
                    # Remove switch from controller's M2M relation in DB
                    current_controller.switches.remove(device)

                # --- 3b. Add New Controller to Device ---
                if new_controller:
                    logger.info(f"Assigning bridge {bridge_name} to new controller {new_controller.device.lan_ip_address}")
                    connect_controller_playbook = 'connect-to-controller'
                    connect_controller_vars = {
                        'ip_address': lan_ip_address,
                        'bridge_name': bridge_name,
                        'controller_ip': new_controller.device.lan_ip_address,
                        'controller_port': new_controller.port_num
                    }
                    assign_controller_result = run_playbook_with_extravars(
                        connect_controller_playbook, playbook_dir_path, inv_path, connect_controller_vars
                    )
                    if assign_controller_result.get('status') == 'failed':
                        error_detail = assign_controller_result.get('error', 'Unknown Ansible error')
                        logger.error(f"Playbook '{connect_controller_playbook}' failed for {bridge_name}: {error_detail}")
                        raise Exception(f'Failed to assign new controller to bridge via Ansible: {error_detail}')
                    # Add switch to new controller's M2M relation in DB
                    new_controller.switches.add(device)

                # Update the bridge's controller field in the database object (will be saved later)
                original_bridge.controller = new_controller

            # --- 4. Update Monitors if API URL or Ports Changed ---
            run_monitors = api_url_changed or ports_changed
            if run_monitors:
                 monitor_api_url = original_bridge.api_url # Use the potentially updated URL
                 if monitor_api_url: # Only run if api_url is set
                    logger.info(f"API URL or ports changed for {bridge_name}, updating monitors...")
                    monitor_vars = {
                        'ip_address': lan_ip_address,
                        'bridge_name': bridge_name,
                        'openflow_version': 'openflow13', # Or from request/config
                        'api_url': monitor_api_url
                    }
                    # Run Flow Monitor
                    install_flow_monitor_result = run_playbook_with_extravars(
                        'run-ovs-flow-monitor', playbook_dir_path, inv_path, monitor_vars
                    )
                    if install_flow_monitor_result.get('status') == 'failed':
                        logger.warning(f'Failed to update flow monitor for bridge {bridge_name} during edit.')
                        # Decide if this should be a hard failure or just a warning

                    # Update QoS Monitor
                    logger.info(f"Updating qos monitor for bridge {bridge_name} during edit.")
                    install_qos_monitor_result = run_playbook_with_extravars(install_qos_monitor, playbook_dir_path, inv_path, monitor_vars)

                    if install_qos_monitor_result.get('status') == 'failed':
                        logger.warning(f'Failed to update qos monitor for bridge {bridge_name} during edit.')
                 elif api_url_changed and not monitor_api_url:
                     logger.info(f"API URL removed for bridge {bridge_name}. Consider stopping monitors if applicable.")
                     # Add logic here to stop/remove monitors if necessary


            # --- 5. Save Bridge Model Changes ---
            if bridge_needs_save:
                logger.info(f"Saving changes to bridge {bridge_name} model (API URL/Controller).")
                original_bridge.save(update_fields=['api_url', 'controller']) # Save only changed fields

            # --- 6. Return Success ---
            logger.info(f"Bridge {bridge_name} updated successfully on device {lan_ip_address}.")
            return Response({'status': 'success', 'message': f'Bridge {bridge_name} updated successfully.'}, status=status.HTTP_200_OK)

        # --- Exception Handling ---
        except Bridge.DoesNotExist:
             logger.warning(f"Edit failed: Bridge {bridge_name} not found on device {lan_ip_address}.")
             return Response({'status': 'error', 'message': 'Bridge not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Device.DoesNotExist:
             logger.warning(f"Edit failed: Device {lan_ip_address} not found.")
             return Response({'status': 'error', 'message': 'Device not found.'}, status=status.HTTP_404_NOT_FOUND)
        # Controller.DoesNotExist is handled by ValidationError now
        except ValidationError as e:
            logger.warning(f'Validation error during bridge edit: {e}')
            messages = getattr(e, 'message_dict', str(e))
            return Response({'status': 'error', 'message': messages}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Catches exceptions raised within the transaction (e.g., playbook failures)
            logger.error(f'Unhandled error in EditBridge for {bridge_name}: {str(e)}', exc_info=True)
            return Response({'status': 'error', 'message': f'An internal error occurred during bridge update: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CreateBridge(APIView):

    @transaction.atomic # Ensure all DB operations succeed or fail together
    def post(self, request):
        try:
            data = request.data
            lan_ip_address = data.get('lan_ip_address')
            validate_ipv4_address(lan_ip_address)
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address,device_type='switch')

            bridge_name = data.get('name')
            api_url = data.get('api_url') # Can be None
            ports_to_add = data.get('ports', [])

            if not bridge_name:
                 return Response({'status': 'error', 'message': 'Bridge name is required.'},
                                status=status.HTTP_400_BAD_REQUEST)

            if Bridge.objects.filter(device=device, name=bridge_name).exists():
                return Response({'status': 'error', 'message': f'A bridge named "{bridge_name}" already exists for device {lan_ip_address}.'},
                                status=status.HTTP_400_BAD_REQUEST)

            # --- Prepare Ansible ---
            inv_content = create_inv_data(lan_ip_address, device.username, device.password)
            inv_path = create_temp_inv(inv_content)

            # --- 1. Create Bridge Structure on Device ---
            create_bridge_playbook = 'ovs-bridge-setup'
            create_bridge_vars = {
                'ip_address': lan_ip_address,
                'bridge_name': bridge_name
            }
            logger.info(f"Running playbook '{create_bridge_playbook}' for bridge {bridge_name} on {lan_ip_address}")
            create_bridge_result = run_playbook_with_extravars(
                create_bridge_playbook, playbook_dir_path, inv_path, create_bridge_vars
            )
            if create_bridge_result.get('status') == 'failed':
                error_detail = create_bridge_result.get('error', 'Unknown Ansible error')
                logger.error(f"Playbook '{create_bridge_playbook}' failed for {bridge_name}: {error_detail}")
                raise Exception(f"Failed to create bridge structure via Ansible: {error_detail}") # Raise to rollback

            # --- 2. Add Ports to Bridge on Device (if any specified) ---
            if ports_to_add:
                add_ports_playbook = 'ovs-port-setup'
                add_ports_vars = {
                    'bridge_name': bridge_name,
                    'ip_address': lan_ip_address,
                    'interfaces': ports_to_add,
                    # 'api_url': api_url
                }
                logger.info(f"Running playbook '{add_ports_playbook}' for bridge {bridge_name} with ports {ports_to_add}")
                add_interfaces_result = run_playbook_with_extravars(
                    add_ports_playbook, playbook_dir_path, inv_path, add_ports_vars
                )
                if add_interfaces_result.get('status') == 'failed':
                    error_detail = add_interfaces_result.get('error', 'Unknown Ansible error')
                    logger.error(f"Playbook '{add_ports_playbook}' failed for {bridge_name}: {error_detail}")
                    # TODO delete the bridge created in step 1 before raising
                    raise Exception(f"Failed to add interfaces to bridge via Ansible: {error_detail}") # Raise to rollback

            # --- 3. Get Bridge Details (DPID) ---
            get_details_playbook = 'ovs-bridge-details'
            get_details_vars = {
                'bridge_name': bridge_name,
                'ip_address': lan_ip_address,
                'openflow_version': 'Openflow13',
            }
            logger.info(f"Running playbook '{get_details_playbook}' for bridge {bridge_name}")
            get_bridge_details_result = run_playbook_with_extravars(
                get_details_playbook, playbook_dir_path, inv_path, get_details_vars, quiet=False
            )

            if get_bridge_details_result.get('status') == 'failed':
                 error_detail = get_bridge_details_result.get('error', 'Unknown Ansible error')
                 logger.error(f"Playbook '{get_details_playbook}' failed for {bridge_name}: {error_detail}")
                 raise Exception(f"Failed to get bridge details (DPID) via Ansible: {error_detail}")

            # Ensure format function handles potential errors in results
            bridge_details = format_ovs_show_bridge_command(get_bridge_details_result.get('results', {}))
            dpid = bridge_details.get('dpid')
            if not dpid:
                 logger.error(f"Could not extract DPID for bridge {bridge_name} from playbook results.")
                 raise Exception(f"Failed to determine DPID for bridge {bridge_name}.")
            cleaned_hex_dpid = dpid.lower().replace('"', '')
            if cleaned_hex_dpid.startswith("0x"):
                cleaned_hex_dpid = cleaned_hex_dpid[2:]
            odl_node_id = None
            try:
                decimal_dpid_val = int(cleaned_hex_dpid, 16)
                odl_node_id = f"openflow:{decimal_dpid_val}"
                logger.info(
                    f"Calculated ODL Node ID for bridge {bridge_name} (DPID: {cleaned_hex_dpid}): {odl_node_id}")
            except ValueError:
                logger.error(
                    f"Invalid DPID format '{cleaned_hex_dpid}' for bridge {bridge_name}. Cannot generate ODL Node ID.")
                # raise Exception(f"Invalid DPID format for bridge {bridge_name}, cannot create ODL Node ID.")
            except TypeError:  # Handles if cleaned_hex_dpid is None (though 'if not hex_dpid' should catch it)
                logger.error(f"DPID is None or invalid for bridge '{bridge_name}' after cleaning.")

            # --- 4. Handle Controller Connection (if specified) ---
            controller = None
            if data.get('controller_ip'):
                controller_port = data.get('controller_port')
                controller_ip = data.get('controller_ip')
                if not controller_port:
                     raise ValidationError("Controller port is required when controller IP is provided.")

                try:
                    # Use get_object_or_404 for related objects within transaction
                    controller_device = get_object_or_404(Device, lan_ip_address=controller_ip,device_type="controller")
                    controller = get_object_or_404(Controller, device=controller_device)
                except (Device.DoesNotExist, Controller.DoesNotExist) as e:
                     logger.error(f"Controller lookup failed: {e}")
                     raise ValidationError(f"Specified controller (IP: {controller_ip}) not found in the database.") from e


                connect_controller_playbook = 'connect-to-controller'
                connect_controller_vars = {
                    'ip_address': lan_ip_address,
                    'controller_port': controller_port,
                    'controller_ip': controller_ip,
                    'bridge_name': bridge_name
                }
                logger.info(f"Running playbook '{connect_controller_playbook}' for bridge {bridge_name} to controller {controller_ip}:{controller_port}")
                assign_controller_result = run_playbook_with_extravars(
                    connect_controller_playbook, playbook_dir_path, inv_path, connect_controller_vars
                )
                if assign_controller_result.get('status') == 'failed':
                    error_detail = assign_controller_result.get('error', 'Unknown Ansible error')
                    logger.error(f"Playbook '{connect_controller_playbook}' failed for {bridge_name}: {error_detail}")
                    raise Exception(f"Failed to connect bridge to controller via Ansible: {error_detail}")

            # --- 5. Create Bridge Object in Database ---
            logger.info(f"Creating bridge record for {bridge_name} in database.")
            bridge = Bridge.objects.create(
                name=bridge_name,
                device=device,
                dpid=dpid,
                controller=controller, # Will be None if no controller specified
                api_url=api_url,
                odl_node_id=odl_node_id
            )
            # Link controller M2M if controller was assigned
            if controller:
                controller.switches.add(device)

            # --- 6. Get OVS Port Numbers (if ports were added) ---
            ovs_port_map = {}
            if ports_to_add:
                get_ovs_nums_playbook = 'get-ovs-port-numbers'
                get_ovs_nums_vars = {
                    'bridge_name': bridge_name,
                    'interfaces': ports_to_add,
                    'ip_address': lan_ip_address,
                }
                logger.info(f"Running playbook '{get_ovs_nums_playbook}' for bridge {bridge_name}")
                get_ovs_nums_result = run_playbook_with_extravars(
                    get_ovs_nums_playbook, playbook_dir_path, inv_path, get_ovs_nums_vars
                )

                ovs_port_map = extract_ovs_port_map(get_ovs_nums_result) # Use the formatter

                if not ovs_port_map:
                    # Check if the playbook *failed* vs just didn't return the map
                    if get_ovs_nums_result.get('status') == 'failed':
                         error_detail = get_ovs_nums_result.get('error', 'Extraction failed')
                         logger.error(f"Playbook '{get_ovs_nums_playbook}' failed for {bridge_name}: {error_detail}")
                         raise Exception(f"Failed to execute OVS port number retrieval: {error_detail}")
                    else:
                         # Playbook succeeded but map couldn't be extracted - critical issue
                         logger.error(f"Failed to parse OVS port numbers for bridge {bridge_name} even after successful port setup and playbook run.")
                         raise Exception(f"Critical error: Could not determine OVS port numbers for bridge {bridge_name} after port setup.")

            # --- 7. Update Port Models in DB (The *only* place ports are linked) ---
            for port_name in ports_to_add:
                try:
                    # Use get_or_create to handle ports that might not exist in DB yet
                    port_obj, created = Port.objects.get_or_create(
                        name=port_name,
                        device=device
                        # Add defaults here if needed for new ports
                    )
                    port_obj.bridge = bridge
                    port_obj.ovs_port_number = ovs_port_map.get(port_name) # Get number or None
                    port_obj.save(update_fields=['bridge', 'ovs_port_number'])

                    if created:
                        logger.info(f"Created new port entry for {port_name} on device {device.name}.")
                    if port_obj.ovs_port_number is None:
                        logger.warning(f"Port {port_name} added to bridge {bridge_name} but OVS port number was not found/assigned.")

                except Exception as e:
                    # Catch specific errors if possible, otherwise log and raise generic
                    logger.error(f"Error updating port {port_name} DB record for bridge {bridge_name}: {e}", exc_info=True)
                    raise Exception(f"Database error while updating port {port_name} for bridge {bridge_name}.") from e


            # --- 8. Install Monitors (Optional, only if api_url provided) ---
            if api_url:
                monitor_vars = {
                    'ip_address': lan_ip_address,
                    'bridge_name': bridge_name,
                    'openflow_version': 'openflow13', # Make dynamic if needed
                    'api_url': api_url
                }
                # Install Flow Monitor
                logger.info(f"Running playbook 'run-ovs-flow-monitor' for bridge {bridge_name}")
                install_flow_monitor_result = run_playbook_with_extravars(
                    'run-ovs-flow-monitor', playbook_dir_path, inv_path, monitor_vars
                )
                if install_flow_monitor_result.get('status') == 'failed':
                    # Log as warning
                    logger.error(f"Failed to install flow monitor for bridge {bridge_name}. Bridge created, but monitoring may be inactive.")
                    raise Exception(
                        f"Critical error: Could not install Flow Monitor for {bridge_name}.")


            # --- 9. Return Success ---
            logger.info(f"Bridge {bridge_name} created successfully on device {lan_ip_address}.")
            return Response({'status': 'success', 'message': f'Bridge {bridge_name} created successfully.'},
                            status=status.HTTP_201_CREATED)

        # --- Exception Handling ---
        except ValidationError as e:
            logger.warning(f'Validation error during bridge creation: {e}')
            # Extract user-friendly messages if possible
            messages = getattr(e, 'message_dict', str(e))
            return Response({'status': 'error', 'message': messages}, status=status.HTTP_400_BAD_REQUEST)
        except Device.DoesNotExist:
             logger.warning(f"Device with IP {lan_ip_address} not found.")
             return Response({'status': 'error', 'message': 'Device not found.'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            # Exceptions raised within the transaction block will trigger rollback
            logger.error(f'Unhandled error in CreateBridge: {str(e)}', exc_info=True)
            # Return the specific error message if it was one we raised deliberately
            return Response({'status': 'error', 'message': f'An internal error occurred: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeleteBridge(APIView):
    @transaction.atomic # Ensure atomicity for the delete operation
    def post(self, request):
        """
        Delete bridge from device and database.
        Clears OVS port numbers for associated ports.
        """
        try:
            data = request.data
            lan_ip_address = data.get('lan_ip_address')
            validate_ipv4_address(lan_ip_address)
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address,device_type="switch")

            bridge_name = data.get('name')
            if not bridge_name:
                 return Response({'status': 'error', 'message': 'Bridge name is required for deletion.'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Find the bridge within the transaction
            try:
                # Use select_for_update if high concurrency is a concern, otherwise optional
                # bridge = Bridge.objects.select_for_update().get(device=device, name=bridge_name)
                bridge = Bridge.objects.get(device=device, name=bridge_name)
            except Bridge.DoesNotExist:
                logger.warning(f"Deletion failed: Bridge {bridge_name} not found on device {lan_ip_address}.")
                return Response({'status': 'error', 'message': 'Bridge not found.'},
                                status=status.HTTP_404_NOT_FOUND)

            # --- 1. Identify associated ports BEFORE deleting bridge ---
            associated_ports = Port.objects.filter(bridge=bridge)
            associated_port_pks = list(associated_ports.values_list('pk', flat=True)) # Get PKs for update
            associated_port_names = list(associated_ports.values_list('name', flat=True)) # Get port names for cleanup

            # prepare ansible inventory
            inv_content = create_inv_data(lan_ip_address, device.username, device.password)
            inv_path = create_temp_inv(inv_content)

            # --- 2. Cleanup port setup effects if bridge has ports ---
            # This removes cron jobs, scripts, and netplan config created by ovs-port-setup
            if associated_port_names:
                logger.info(f"Cleaning up port setup effects for bridge {bridge_name} with ports: {associated_port_names}")
                cleanup_port_setup_vars = {
                    'interfaces': associated_port_names,
                    'ip_address': lan_ip_address,
                }
                cleanup_port_setup_result = run_playbook_with_extravars(
                    'ovs-cleanup-port-setup', playbook_dir_path, inv_path, cleanup_port_setup_vars
                )
                if cleanup_port_setup_result.get('status') == 'failed':
                    error_detail = cleanup_port_setup_result.get('error', 'Unknown Ansible error')
                    logger.warning(f"Failed to cleanup port setup effects for bridge {bridge_name}: {error_detail}")
                    # Don't fail the deletion for cleanup issues, just log them
                else:
                    logger.info(f"Successfully cleaned up port setup effects for bridge {bridge_name}")

            # --- 3. Cleanup controller automation if bridge has a controller ---
            # This removes controller connection, automation scripts, cron jobs, and log files
            if bridge.controller:
                logger.info(f"Cleaning up controller automation for bridge {bridge_name} with controller {bridge.controller.device.lan_ip_address}")
                cleanup_controller_vars = {
                    'bridge_name': bridge_name,
                    'ip_address': lan_ip_address,
                }
                cleanup_controller_result = run_playbook_with_extravars(
                    'ovs-cleanup-controller-automation', playbook_dir_path, inv_path, cleanup_controller_vars
                )
                if cleanup_controller_result.get('status') == 'failed':
                    error_detail = cleanup_controller_result.get('error', 'Unknown Ansible error')
                    logger.warning(f"Failed to cleanup controller automation for bridge {bridge_name}: {error_detail}")
                    # Don't fail the deletion for cleanup issues, just log them
                else:
                    logger.info(f"Successfully cleaned up controller automation for bridge {bridge_name}")

            # --- 4. Cleanup flow monitoring if bridge has an API URL ---
            if bridge.api_url:
                logger.info(f"Cleaning up flow monitoring for bridge {bridge_name} with API URL: {bridge.api_url}")
                cleanup_flow_monitoring_vars = {
                    'bridge_name': bridge_name,
                    'ip_address': lan_ip_address,
                }
                cleanup_flow_monitoring_result = run_playbook_with_extravars(
                    'ovs-cleanup-flow-monitoring', playbook_dir_path, inv_path, cleanup_flow_monitoring_vars
                )
                if cleanup_flow_monitoring_result.get('status') == 'failed':
                    error_detail = cleanup_flow_monitoring_result.get('error', 'Unknown Ansible error')
                    logger.warning(f"Failed to cleanup flow monitoring for bridge {bridge_name}: {error_detail}")
                    # Don't fail the deletion for cleanup issues, just log them
                else:
                    logger.info(f"Successfully cleaned up flow monitoring for bridge {bridge_name}")

            # --- 5. Cleanup port monitoring if bridge has ports ---
            # Port monitoring is only installed when bridge has ports assigned
            if associated_port_names:
                logger.info(f"Cleaning up port monitoring for bridge {bridge_name} with ports: {associated_port_names}")
                cleanup_port_monitoring_vars = {
                    'bridge_name': bridge_name,
                    'ip_address': lan_ip_address,
                }
                cleanup_port_monitoring_result = run_playbook_with_extravars(
                    'ovs-cleanup-port-monitoring', playbook_dir_path, inv_path, cleanup_port_monitoring_vars
                )
                if cleanup_port_monitoring_result.get('status') == 'failed':
                    error_detail = cleanup_port_monitoring_result.get('error', 'Unknown Ansible error')
                    logger.warning(f"Failed to cleanup port monitoring for bridge {bridge_name}: {error_detail}")
                    # Don't fail the deletion for cleanup issues, just log them
                else:
                    logger.info(f"Successfully cleaned up port monitoring for bridge {bridge_name}")

            # --- 6. Cleanup sniffer if installed for this bridge ---
            # The sniffer is installed if a SnifferInstallationConfig exists for this device and bridge
            try:
                sniffer_installation = PluginInstallation.objects.get(device=device, plugin__name='tau-traffic-classification-sniffer')
                sniffer_config = SnifferInstallationConfig.objects.get(installation=sniffer_installation, bridge_name=bridge_name)
                logger.info(f"Cleaning up sniffer for bridge {bridge_name} on device {lan_ip_address}")
                # --- Uninstall sniffer from device ---
                uninstall_result = uninstall_sniffer_util(lan_ip_address)
                if uninstall_result.get('status') != 'success':
                    logger.error(f"Failed to uninstall sniffer from device {lan_ip_address}: {uninstall_result.get('message')}")
                    raise Exception(f"Failed to uninstall sniffer from device {lan_ip_address}: {uninstall_result.get('message')}")
                else:
                    logger.info(f"Successfully uninstalled sniffer from device {lan_ip_address}")
                # Optionally, delete the sniffer config and installation from DB
                sniffer_config.delete()
                sniffer_installation.delete()
            except (PluginInstallation.DoesNotExist, SnifferInstallationConfig.DoesNotExist):
                logger.info(f"No sniffer installed for bridge {bridge_name} on device {lan_ip_address}, skipping sniffer uninstall.")

            # --- 7. Run Ansible playbook to delete the bridge from the device ---
            logger.info(f"Attempting to delete bridge {bridge_name} from device {lan_ip_address} via Ansible.")
            inv_content = create_inv_data(lan_ip_address, device.username, device.password)
            inv_path = create_temp_inv(inv_content)
            delete_bridge_playbook = 'ovs-delete-bridge'
            delete_bridge_vars = {
                'bridge_name': bridge_name,
                'ip_address': lan_ip_address,
            }
            delete_bridge_result = run_playbook_with_extravars(
                delete_bridge_playbook, playbook_dir_path, inv_path, delete_bridge_vars
            )

            # Check result - fail transaction if Ansible fails
            if delete_bridge_result.get('status') != 'success':
                 # Log the error from Ansible if available
                 ansible_error = delete_bridge_result.get('error', 'Unknown Ansible error')
                 logger.error(f"Ansible failed to delete bridge {bridge_name} on {lan_ip_address}: {ansible_error}")
                 # Check if the error indicates the bridge didn't exist - maybe proceed?
                 # Example check (adjust based on actual Ansible error message):
                 if "does not exist" in ansible_error.lower():
                      logger.warning(f"Ansible reported bridge {bridge_name} already absent. Proceeding with DB cleanup.")
                 else:
                      raise Exception(f'Failed to delete bridge {bridge_name} on the device via Ansible.') # Rollback transaction

            # --- 8. Update associated ports in the database ---
            # Set ovs_port_number to None. Bridge FK is handled by on_delete=SET_NULL.
            if associated_port_pks:
                logger.info(f"Clearing OVS port numbers for ports previously associated with bridge {bridge_name}.")
                updated_count = Port.objects.filter(pk__in=associated_port_pks).update(ovs_port_number=None)
                logger.info(f"Cleared OVS number for {updated_count} ports.")

            # --- 9. Delete the bridge interface port itself if it exists ---
            # OVS often creates a port with the same name as the bridge
            try:
                bridge_interface_port = Port.objects.get(device=device, name=bridge_name)
                logger.info(f"Deleting port entry named '{bridge_name}' associated with the bridge.")
                bridge_interface_port.delete()
            except Port.DoesNotExist:
                logger.info(f"No port entry named '{bridge_name}' found to delete.")
                pass # No port named after the bridge, which is fine

            # --- 10. Delete the bridge from the database ---
            bridge_pk = bridge.pk # Get pk for logging
            logger.info(f"Deleting bridge {bridge_name} (PK: {bridge_pk}) from database.")
            bridge.delete()

            # --- 11. Return Success ---
            logger.info(f"Bridge {bridge_name} deleted successfully from device {lan_ip_address} and database.")
            # 204 No Content is also appropriate for successful deletions
            return Response({'status': 'success', 'message': f'Bridge {bridge_name} deleted successfully.'},
                            status=status.HTTP_204_NO_CONTENT)

        # --- Exception Handling ---
        except Device.DoesNotExist: # Should be caught by initial get_object_or_404
             logger.error(f"Deletion failed: Device {lan_ip_address} not found.")
             return Response({'status': 'error', 'message': 'Device not found.'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            logger.warning(f'Validation error during bridge deletion: {e}')
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Catches exceptions raised within the transaction (like Ansible failure)
            logger.error(f'Unhandled error in DeleteBridge for {bridge_name} on {lan_ip_address}: {str(e)}', exc_info=True)
            return Response({'status': 'error', 'message': f'An internal error occurred during bridge deletion: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class AssignPortsView(APIView):
    def post(self, request):
        try:
            data = request.data
            lan_ip_address = data.get('lan_ip_address')
            validate_ipv4_address(lan_ip_address)
        except ValidationError:
            return Response({'status': 'error', 'message': 'Invalid IP address format.'},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteControllerView(APIView):
    def delete(self, request):
        try:
            data = request.data
            controller_ip = data.get('controller_ip')
            validate_ipv4_address(controller_ip)
            controller = get_object_or_404(Controller, lan_ip_address=controller_ip)

            with transaction.atomic():
                switches = controller.switches.all()
                for switch in switches:
                    bridges = switch.bridges.all()
                    for bridge in bridges:
                        if bridge.controller == controller:

                            bridge_name = bridge.name
                            device = bridge.device
                            lan_ip_address = device.lan_ip_address
                            save_bridge_name_to_config(bridge_name, config_path)
                            write_to_inventory(lan_ip_address, device.username, device.password, inventory_path)
                            save_ip_to_config(lan_ip_address, config_path)
                            delete_controller = run_playbook('remove-controller', playbook_dir_path, inventory_path)
                            if delete_controller.get('status') == 'success':
                                bridge.controller = None
                                bridge.save()
                            else:
                                return Response({'status': 'failed',
                                                 'message': 'Unable to delete controller due to external system failure.'},
                                                status=status.HTTP_400_BAD_REQUEST)
                controller.delete()
            return Response({'status': 'success', 'message': 'Controller and its references successfully deleted.'},
                            status=status.HTTP_202_ACCEPTED)

        except ValidationError:
            return Response({'status': 'error', 'message': 'Invalid IP address format.'},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

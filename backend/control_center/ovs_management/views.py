import os
import time

from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework.response import Response

from ovs_install.utilities.services.ovs_port_setup import setup_ovs_port
from ovs_install.utilities.ansible_tasks import run_playbook
from ovs_install.utilities.utils import check_system_details
from ovs_install.utilities.ovs_results_format import format_ovs_show
from general.models import Device, Bridge, Port
from django.shortcuts import get_object_or_404
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError
import logging
from general.serializers import BridgeSerializer
from ovs_install.utilities.utils import write_to_inventory, save_ip_to_config, save_bridge_name_to_config, \
    save_interfaces_to_config, save_controller_port_to_config, save_controller_ip_to_config

from general.models import Controller

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
logger = logging.getLogger(__name__)
install_ovs = "install-ovs"
get_ports = "get-ports"
ovs_show = 'ovs-show'
playbook_dir_path = f"{parent_dir}/ansible/playbooks"
inventory_path = f"{parent_dir}/ansible/inventory/inventory"
config_path = f"{parent_dir}/ansible/group_vars/all.yml"


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
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address)

            # Assuming run_playbook and check_system_details are implemented and return interface names
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
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address)

            # Assuming run_playbook and check_system_details are implemented and return interface names
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

            # get unassociated ports and return them:
            bridges = device.bridges.all()
            bridge_names = [bridge.name for bridge in bridges]
            ports = device.ports.all()
            # Filter ports that are not assigned to any bridge and whose names do not match any bridge names
            unassigned_ports = [port for port in ports if port.bridge is None and port.name not in bridge_names and port.name != 'ovs-system']
            # Extracting interface names for the response
            unassigned_interface_names = [port.name for port in unassigned_ports]
            print(f'Unassigned ports: {unassigned_ports}')
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


class GetDeviceBridges(APIView):
    def get(self, request, lan_ip_address):
        try:
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


class CreateBridge(APIView):
    def post(self, request):
        try:

            data = request.data
            lan_ip_address = data.get('lan_ip_address')
            validate_ipv4_address(lan_ip_address)
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address)

            bridge_name = data.get('name')

            if Bridge.objects.filter(device=device, name=bridge_name).exists():
                return Response({'status': 'error', 'message': 'A bridge with this name already exists for the device'},
                                status=status.HTTP_400_BAD_REQUEST)

            open_flow_version = data.get('openFlowVersion')
            ports = data.get('ports')
            save_bridge_name_to_config(bridge_name, config_path)
            write_to_inventory(lan_ip_address, device.username, device.password, inventory_path)
            save_ip_to_config(lan_ip_address, config_path)
            save_interfaces_to_config(ports, config_path)
            create_bridge = run_playbook('ovs-bridge-setup', playbook_dir_path, inventory_path)

            if create_bridge['status'] == 'failed':
                return Response({'status': 'error', 'message': 'error creating bridge'},
                                status=status.HTTP_400_BAD_REQUEST)
            if data.get('controller_ip'):
                port = data.get('controller_port')
                controller_ip = data.get('controller_ip')
                controller = get_object_or_404(Controller, lan_ip_address=controller_ip)

                save_controller_port_to_config(port, config_path)
                save_controller_ip_to_config(controller_ip, config_path)
                assign_controller = run_playbook('connect-to-controller', playbook_dir_path, inventory_path)
                if assign_controller['status'] == 'failed':
                    return Response({'status': 'error', 'message': 'error creating bridge'},
                                    status=status.HTTP_400_BAD_REQUEST)
                controller.switches.add(device)
                bridge = Bridge.objects.create(
                    name=data.get('name'),
                    device=device,
                    dpid='123',
                    controller=controller,
                )
            else:
                bridge = Bridge.objects.create(
                    name=data.get('name'),
                    device=device,
                    dpid='123',
                )

            add_interfaces = run_playbook('ovs-port-setup', playbook_dir_path, inventory_path)
            if add_interfaces['status'] == 'failed':
                return Response({'status': 'error', 'message': f'error adding interfaces to  bridge {bridge_name}'},
                                status=status.HTTP_400_BAD_REQUEST)
            for i in ports:
                port = Port.objects.get(
                    name=i,
                )
                port.bridge = bridge
                port.device = device
                port.save(update_fields=['bridge', 'device'])
            return Response({'status': 'success', 'message': f'Bridge {bridge_name} created successfully.'},
                            status=status.HTTP_201_CREATED)
        # TODO on fail delete bridge if it has been created
        except ValidationError as e:
            logger.error(f'Validation error: {str(e)}', exc_info=True)
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f'Error in CreateBridge: {str(e)}', exc_info=True)
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteBridge(APIView):
    def post(self, request):
        try:
            data = request.data
            lan_ip_address = data.get('lan_ip_address')
            validate_ipv4_address(lan_ip_address)
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address)
            bridge_name = data.get('name')


            with transaction.atomic():
                bridge = Bridge.objects.filter(device=device, name=bridge_name).first()
                if bridge:
                    save_bridge_name_to_config(bridge_name, config_path)
                    write_to_inventory(lan_ip_address, device.username, device.password, inventory_path)
                    save_ip_to_config(lan_ip_address, config_path)
                    delete_bridge = run_playbook('ovs-delete-bridge', playbook_dir_path, inventory_path)
                    if delete_bridge.get('status') == 'success':
                        # Delete the bridge from the database
                        if Port.objects.filter(name=bridge.name).exists():
                            port_to_del = Port.objects.get(name=bridge.name)
                            port_to_del.delete()
                        bridge.delete()

                        return Response({'status': 'success', 'message': f'Bridge {bridge_name} deleted successfully.'},
                                        status=status.HTTP_202_ACCEPTED)
                    else:
                        return Response({'status': 'failed', 'message': 'Unable to delete bridge due to external system failure.'},
                                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'status': 'error', 'message': 'Bridge not found.'},
                                status=status.HTTP_404_NOT_FOUND)
        except ValidationError:
            return Response({'status': 'error', 'message': 'Invalid IP address format.'},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)},
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

from django.db import transaction

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
                            print(lan_ip_address)
                            print(bridge_name)
                            save_bridge_name_to_config(bridge_name, config_path)
                            write_to_inventory(lan_ip_address, device.username, device.password, inventory_path)
                            save_ip_to_config(lan_ip_address, config_path)
                            delete_controller = run_playbook('remove-controller', playbook_dir_path, inventory_path)
                            if delete_controller.get('status') == 'success':
                                bridge.controller = None
                                bridge.save()
                            else:
                                return Response({'status': 'failed', 'message': 'Unable to delete controller due to external system failure.'},
                                                status=status.HTTP_400_BAD_REQUEST)
                controller.delete()
            return Response({'status': 'success', 'message': 'Controller and its references successfully deleted.'},
                            status=status.HTTP_202_ACCEPTED)

        except ValidationError:
            return Response({'status': 'error', 'message': 'Invalid IP address format.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

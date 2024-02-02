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

from ovs_install.utilities.utils import write_to_inventory, save_ip_to_config, save_bridge_name_to_config, save_interfaces_to_config

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
        try:
            validate_ipv4_address(lan_ip_address)

            result = run_playbook(get_ports, playbook_dir_path, inventory_path)
            interfaces = check_system_details(result)

            return Response({"status": "success", "interfaces": interfaces})
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
                return Response({'status': 'error', 'message': result['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
                return Response({'status': 'error', 'message': 'error creating bridge'}, status=status.HTTP_400_BAD_REQUEST)
            bridge = Bridge.objects.create(
                name=data.get('name'),
                device=device,
                dpid='123',
            )
            add_interfaces = run_playbook('ovs-port-setup', playbook_dir_path, inventory_path)
            if add_interfaces['status'] == 'failed':
                return Response({'status': 'error', 'message': f'error adding interfaces to  bridge {bridge_name}'}, status=status.HTTP_400_BAD_REQUEST)
            for i in ports:
                port = Port.objects.get(
                    name=i,
                )
                port.bridge = bridge
                port.device = device
                port.save(update_fields=['bridge', 'device'])
            return Response({'status': 'success', 'message': f'Bridge {bridge_name} created successfully.'},
                            status=status.HTTP_201_CREATED)

        except ValidationError as e:
            logger.error(f'Validation error: {str(e)}', exc_info=True)
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f'Error in CreateBridge: {str(e)}', exc_info=True)
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
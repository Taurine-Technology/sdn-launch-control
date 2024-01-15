import os
import time

from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework.response import Response
from ovs_install.utilities.ansible_tasks import run_playbook
from ovs_install.utilities.utils import check_system_details
from ovs_install.utilities.ovs_results_format import format_ovs_show
from general.models import Device
from django.shortcuts import get_object_or_404
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError
import logging

from ovs_install.utilities.utils import write_to_inventory, save_ip_to_config

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
        validate_ipv4_address(lan_ip_address)
        result = run_playbook(ovs_show, playbook_dir_path, inventory_path)
        bridges = format_ovs_show(result)
        print(bridges)
        return Response({'status': 'success', 'bridges': bridges},
                        status=status.HTTP_200_OK)
class CreateBridge(APIView):
    def post(self, request):
        try:
            data = request.data
            bridge_name = data.get('name')
            open_flow_version = data.get('openFlowVersion')
            ports = data.get('ports')

            time.sleep(2)

            return Response({'status': 'success', 'message': f'Bridge {bridge_name} created successfully.'},
                            status=status.HTTP_201_CREATED)

        except ValidationError as e:
            logger.error(f'Validation error: {str(e)}', exc_info=True)
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f'Error in CreateBridge: {str(e)}', exc_info=True)
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
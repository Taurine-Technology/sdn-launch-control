import os

from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework.response import Response
from .utilities.ansible_tasks import run_playbook
from general.models import Device, Port
from .utilities.utils import check_system_details
from django.shortcuts import get_object_or_404
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError
import logging

from .utilities.utils import write_to_inventory, save_ip_to_config

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
logger = logging.getLogger(__name__)
test_server = "install-ovs"
playbook_dir_path = f"{parent_dir}/ansible/playbooks"
inventory_path = f"{parent_dir}/ansible/inventory/inventory"
config_path = f"{parent_dir}/ansible/group_vars/all.yml"
get_ports = "get-ports"


class InstallOvsView(APIView):
    def post(self, request):
        try:
            data = request.data
            print(data)
            print('about to run')
            lan_ip_address = data.get('lan_ip_address')
            write_to_inventory(lan_ip_address, data.get('username'), data.get('password'), inventory_path)
            save_ip_to_config(lan_ip_address, config_path)
            run_playbook(test_server, playbook_dir_path, inventory_path)

            result = run_playbook(get_ports, playbook_dir_path, inventory_path)
            interfaces = check_system_details(result)
            print(f'Interfaces: {interfaces}')
            if interfaces is not None:
                num_ports = len(interfaces)
            else:
                num_ports = 0

            device, created = Device.objects.get_or_create(
                lan_ip_address=lan_ip_address,
                defaults={
                    'name': data.get('name'),
                    'device_type': data.get('device_type'),
                    'username': data.get('username'),
                    'password': data.get('password'),
                    'os_type': data.get('os_type'),
                    'ovs_enabled': True,
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
                print('Creating ports')
                for interface in interfaces:
                    port, created_ports = Port.objects.get_or_create(
                        name=interface,
                        defaults={
                            'device': device
                        }
                    )

            message = "OVS Installed." if created else "OVS already installed."
            return Response({"status": "success", "message": message}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

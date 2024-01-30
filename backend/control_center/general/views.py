from django.shortcuts import render

from ovs_install.utilities.ansible_tasks import run_playbook
from ovs_install.utilities.utils import write_to_inventory, save_ip_to_config
import os
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework.response import Response
from .models import Device, Port
from django.shortcuts import get_object_or_404
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError
import logging

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
logger = logging.getLogger(__name__)
test_connection = "test-connection"
playbook_dir_path = f"{parent_dir}/ansible/playbooks"
inventory_path = f"{parent_dir}/ansible/inventory/inventory"
config_path = f"{parent_dir}/ansible/group_vars/all.yml"


# *---------- Network Connectivity Methods ----------*
class CheckDeviceConnectionView(APIView):
    def get(self, request, lan_ip_address):
        try:
            validate_ipv4_address(lan_ip_address)
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address)
            data = {
                "name": device.name,
                "device_type": device.device_type,
                'username': device.username,
                'password': device.password,
                "os_type": device.os_type,
                "lan_ip_address": device.lan_ip_address,
                "ports": device.num_ports,
                "ovs_enabled": device.ovs_enabled,
                "ovs_version": device.ovs_version,
                "openflow_version": device.openflow_version
            }
            write_to_inventory(lan_ip_address, data.get('username'), data.get('password'), inventory_path)
            save_ip_to_config(lan_ip_address, config_path)
            result = run_playbook(test_connection, playbook_dir_path, inventory_path)
            if result['status'] == 'failed':
                print()
                return Response({'status': 'error', 'message': result['error']},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"status": "success"}, status=status.HTTP_200_OK)
        except ValidationError:
            return Response({"status": "error", "message": "Invalid IP address format."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print('CAUGHT AN UNEXPECTED ERROR')
            print(e)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# *---------- Basic device get and post methods ----------*
class AddDeviceView(APIView):
    def post(self, request):
        try:
            data = request.data

            try:
                validate_ipv4_address(data.get('lan_ip_address'))
            except ValidationError:
                return Response({"status": "error", "message": "Invalid IP address format."},
                                status=status.HTTP_400_BAD_REQUEST)
            if data.get('ovs_enabled'):
                ovs_enabled = True
                ports = data.get('ports')
                ovs_version = data.get('ovs_version')
                openflow_version = data.get('openflow_version')
                device = Device.objects.create(
                    name=data.get('name'),
                    device_type=data.get('device_type'),
                    username=data.get('username'),
                    password=data.get('password'),
                    os_type=data.get('os_type'),
                    lan_ip_address=data.get('lan_ip_address'),
                    ports=ports,
                    ovs_enabled=ovs_enabled,
                    ovs_version=ovs_version,
                    openflow_version=openflow_version,
                )
            else:
                device = Device.objects.create(
                    name=data.get('name'),
                    device_type=data.get('device_type'),
                    username=data.get('username'),
                    password=data.get('password'),
                    os_type=data.get('os_type'),
                    lan_ip_address=data.get('lan_ip_address'),
                )

            device.save()
            return Response({"status": "success", "message": "Device added successfully."},
                            status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DeviceListView(APIView):
    def get(self, request):
        try:
            devices = Device.objects.all()
            data = [
                {
                    "name": device.name,
                    "device_type": device.device_type,
                    "os_type": device.os_type,
                    "lan_ip_address": device.lan_ip_address,
                    "ports": device.num_ports,
                    "ovs_enabled": device.ovs_enabled,
                    "ovs_version": device.ovs_version,
                    "openflow_version": device.openflow_version
                } for device in devices
            ]
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e, exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeviceDetailsView(APIView):
    def get(self, request, lan_ip_address):
        try:
            validate_ipv4_address(lan_ip_address)
        except ValidationError:
            return Response({"status": "error", "message": "Invalid IP address format."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address)

            data = {
                "name": device.name,
                "device_type": device.device_type,
                "os_type": device.os_type,
                "lan_ip_address": device.lan_ip_address,
                "ports": device.num_ports,
                "ovs_enabled": device.ovs_enabled,
                "ovs_version": device.ovs_version,
                "openflow_version": device.openflow_version
            }
            print(data)

            return Response({"status": "success", "device": data}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteDeviceView(APIView):
    def delete(self, request):
        data = request.data
        try:
            validate_ipv4_address(data.get('lan_ip_address'))
        except ValidationError:
            return Response({"status": "error", "message": "Invalid IP address format."},
                            status=status.HTTP_400_BAD_REQUEST)

        lan_ip_address = data.get('lan_ip_address')
        device = get_object_or_404(Device, lan_ip_address=lan_ip_address)
        device.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# *---------- OVS get and post methods ----------*
class DeviceBridgesView(APIView):
    def get(self, request, lan_ip_address):
        try:
            # Find the device by LAN IP address
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address)

            # Retrieve bridges related to the device
            bridges = device.bridges.all()
            if bridges.exists():
                bridges_data = [{'name': bridge.name, 'dpid': bridge.dpid} for bridge in bridges]
                return Response({'status': 'success', 'bridges': bridges_data})
            else:
                return Response({'status': 'info', 'message': 'No bridges assigned to this device.'})

        except ValueError:
            # Handle invalid IP address format
            return Response({'status': 'error', 'message': 'Invalid IP address format.'},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Generic error handling
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DevicePortsView(APIView):
    def get(self, request, lan_ip_address):
        try:
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address)
            ports = Port.objects.filter(bridge__device=device)
            if ports.exists():
                ports_data = [{'name': port.name} for port in ports]
                return Response({'status': 'success', 'ports': ports_data})
            else:
                return Response({'status': 'info', 'message': 'No ports assigned to this device.'})
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

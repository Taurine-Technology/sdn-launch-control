from django.shortcuts import render

from ovs_install.utilities.ansible_tasks import run_playbook
from ovs_install.utilities.utils import write_to_inventory, save_ip_to_config, save_bridge_name_to_config, \
    save_interfaces_to_config
import os
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework.response import Response
from .models import Device, Port, Bridge
from django.shortcuts import get_object_or_404
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError
import logging
from .serializers import BridgeSerializer
from .models import Controller

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
                    num_ports=ports,
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

        try:
            lan_ip_address = data.get('lan_ip_address')
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address)
            bridges = Bridge.objects.filter(device=device)
            if bridges:
                for b in bridges:
                    save_bridge_name_to_config(b.name, config_path)
                    write_to_inventory(lan_ip_address, device.username, device.password, inventory_path)
                    save_ip_to_config(lan_ip_address, config_path)
                    delete_bridge = run_playbook('ovs-delete-bridge', playbook_dir_path, inventory_path)
                    if delete_bridge.get('status') == 'success':
                        # Delete the bridge from the database
                        b.delete()
                    else:
                        return Response({'status': 'error', 'message': f'unable to delete bridge {b.name}'},
                                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                device.delete()
            else:
                device.delete()

        except Exception as e:
            return Response({'status': 'error', 'message': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_204_NO_CONTENT)


class UpdateDeviceView(APIView):
    def put(self, request, lan_ip_address):
        try:
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address)
            data = request.data

            # Update fields if they are present in the request
            for field in ['lan_ip_address', 'name', 'device_type', 'os_type', 'username', 'password', 'num_ports',
                          'ovs_enabled',
                          'ovs_version', 'openflow_version']:
                if field in data:
                    if field == 'lan_ip_address':
                        validate_ipv4_address(data[field])
                    setattr(device, field, data[field])

            # Validate and save the device
            device.full_clean()
            device.save()
            return Response({"status": "success", "message": "Device updated successfully."}, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# *---------- OVS get and post methods ----------*
class DeviceBridgesView(APIView):
    def get(self, request, lan_ip_address):
        try:
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address)
            bridges = device.bridges.all()
            if bridges.exists():
                serializer = BridgeSerializer(bridges, many=True)
                print(serializer.data)
                return Response({'status': 'success', 'bridges': serializer.data})
            else:
                return Response({'status': 'info', 'message': 'No bridges assigned to this device.'})
        except ValueError:
            return Response({'status': 'error', 'message': 'Invalid IP address format.'},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
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


# *---------- Controller get and post methods ----------*
class AddControllerView(APIView):
    def post(self, request):
        try:
            data = request.data
            lan_ip_address = data.get('lan_ip_address')
            validate_ipv4_address(lan_ip_address)
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address)
            controller = Controller.objects.create(
                type=data.get('type'),
                device=device,
                lan_ip_address=lan_ip_address,
            )
        except ValidationError:
            return Response({"status": "error", "message": "Invalid IP address format."},
                            status=status.HTTP_400_BAD_REQUEST)


class ControllerListView(APIView):
    def get(self, request):
        try:
            controllers = Controller.objects.all()
            data = [
                {
                    "type": controller.type,
                    "device": controller.device.name,
                    "lan_ip_address": controller.lan_ip_address,
                    "switches": [
                        {
                            "name": switch.name,
                            "lan_ip_address": switch.lan_ip_address,
                        }
                        for switch in controller.switches.all()
                    ],
                } for controller in controllers
            ]
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e, exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

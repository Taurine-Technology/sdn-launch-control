# File: general/views.py
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

from django.shortcuts import render
from django.shortcuts import get_list_or_404
from rest_framework.decorators import action
from ovs_install.utilities.ansible_tasks import run_playbook
from ovs_install.utilities.utils import write_to_inventory, save_ip_to_config, save_bridge_name_to_config, \
    save_interfaces_to_config
import os
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
from .serializers import BridgeSerializer, ControllerSerializer
from .models import Controller, Plugins
from .serializers import DeviceSerializer

from rest_framework.viewsets import ModelViewSet
from .models import Controller
from .serializers import ControllerSerializer
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication
from utils.ansible_utils import run_playbook_with_extravars, create_temp_inv, create_inv_data
# Import the model manager
from classifier.model_manager import model_manager
from odl.models import Category
from classifier.models import ModelConfiguration

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
logger = logging.getLogger(__name__)
test_connection = "test-connection"
playbook_dir_path = f"{parent_dir}/ansible/playbooks"
inventory_path = f"{parent_dir}/ansible/inventory/inventory"
config_path = f"{parent_dir}/ansible/group_vars/all.yml"
from .models import ClassifierModel


# *---------- Network Connectivity Methods ----------*
class CheckDeviceConnectionView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get(self, request, lan_ip_address, device_type):
        try:
            validate_ipv4_address(lan_ip_address)
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address, device_type=device_type)
            # print('### Found device', device)

            inv_content = create_inv_data(lan_ip_address, device.username, device.password)
            inv_path = create_temp_inv(inv_content)
            # write_to_inventory(lan_ip_address, data.get('username'), data.get('password'), inventory_path)
            # save_ip_to_config(lan_ip_address, config_path)
            result = run_playbook_with_extravars(test_connection, playbook_dir_path, inv_path, {
                        'ip_address': lan_ip_address,
                    })
            if result['status'] == 'failed':
                logger.debug(result)
                return Response({'status': 'error', 'message': result['error']},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"status": "success"}, status=status.HTTP_200_OK)
        except ValidationError:
            return Response({"status": "error", "message": "Invalid IP address format."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.debug('CAUGHT AN UNEXPECTED ERROR')
            logger.exception(e)
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


class PluginListView(APIView):
    def get(self, request):
        try:
            plugins = Plugins.objects.all()
            data = [
                {
                    "alias": plugin.alias,
                    "name": plugin.name,
                    "version": plugin.version,
                    "short_description": plugin.short_description,
                    "long_description": plugin.long_description,
                    "author": plugin.author,
                    "installed": plugin.installed,
                } for plugin in plugins
            ]
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e, exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckPluginInstallation(APIView):

    def get(self, request, plugin_name):

        try:
            plugin = Plugins.objects.get(name=plugin_name)
            if plugin_name == 'tau-traffic-classification-sniffer':
                # Check if there are any devices associated with the plugin
                has_devices = plugin.target_devices.exists()
                return JsonResponse({'hasDevices': has_devices}, safe=False)
            else:
                installed = plugin.installed
                return Response({"message": installed},
                                status=status.HTTP_200_OK)
        except Plugins.DoesNotExist:
            return JsonResponse({'hasDevices': False}, safe=False)


class InstallPluginDatabaseAlterView(APIView):
    def post(self, request, plugin_name):
        try:
            plugin = Plugins.objects.get(name=plugin_name)
            plugin.installed = True
            plugin.save()
            return Response({"status": "success", "message": "Plugin installed successfully"},
                            status=status.HTTP_200_OK)
        except Plugins.DoesNotExist as e:
            logger.error(e, exc_info=True)
            return Response({"status": "error", "message": "Plugin not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(e, exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UninstallPluginDatabaseAlterView(APIView):
    def post(self, request, plugin_name):
        try:
            plugin = Plugins.objects.get(name=plugin_name)
            plugin.installed = False
            plugin.save()
            return Response({"status": "success", "message": "Plugin uninstalled successfully"},
                            status=status.HTTP_200_OK)
        except Plugins.DoesNotExist as e:
            logger.error(e, exc_info=True)
            return Response({"status": "error", "message": "Plugin not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(e, exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InstallPluginView(APIView):
    def post(self, request):
        try:
            data = request.data
            name = data.get('name')
            installed = data.get('installed')
            device_ip_address = data.get('lan_ip_address')
            validate_ipv4_address(device_ip_address)

            plugin = Plugins.objects.get(name=name)
            if installed:
                plugin.installed = True
                device = Device.objects.get(lan_ip_address=device_ip_address)
                if not plugin.target_devices.filter(id=device.id).exists():
                    logger.debug(f'adding {device.lan_ip_address}')
                    plugin.target_devices.add(device)
            else:
                plugin.installed = False
            plugin.save()
            return Response({"status": "success", "message": "Plugin installed successfully"},
                            status=status.HTTP_200_OK)
        except ValidationError:
            return Response({"status": "error", "message": "Invalid IP address format."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Device.DoesNotExist:
            return Response({"status": "error", "message": "Device not found"}, status=status.HTTP_404_NOT_FOUND)
        except Plugins.DoesNotExist:
            return Response({"status": "error", "message": "Plugin not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(e, exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeviceListView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
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

class DeviceDetailView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, device_id):
        """
        Returns the details of a specific device by its ID.
        """
        try:
            # Get the device object or return a 404 if it doesn't exist
            device = get_object_or_404(Device, id=device_id)

            # Serialize the device data
            serializer = DeviceSerializer(device)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e, exc_info=True)
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
class DeviceDetailsViewByIp(APIView):
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
            logger.debug(data)

            return Response({"status": "success", "device": data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(e)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ForceDeleteDeviceView(APIView):
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

            # remove links to bridges if this device is a controller
            if Controller.objects.filter(device=device).exists():
                logger.debug(f'{Device.name} is a controller.')
                controller = get_object_or_404(Controller, device=device)
                associated_bridges = controller.bridges.all()
                if associated_bridges:
                    for bridge in associated_bridges:
                        logger.debug(f"Bridge Name: {bridge.name}, Device: {bridge.device.name}")
                        bridge.controller = None
                        bridge.save()
                device.delete()
            else:
                device.delete()

        except Exception as e:
            return Response({'status': 'error', 'message': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_204_NO_CONTENT)


class DeleteDeviceView(APIView):
    def delete(self, request):
        data = request.data
        try:
            logger.debug(data.get('lan_ip_address'))
            validate_ipv4_address(data.get('lan_ip_address'))
        except ValidationError:
            return Response({"status": "error", "message": "Invalid IP address format."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            lan_ip_address = data.get('lan_ip_address')
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address)
            bridges = Bridge.objects.filter(device=device)

            # remove links to bridges if this device is a controller
            if Controller.objects.filter(device=device).exists():
                logger.debug(f'{Device.name} is a controller.')
                controller = get_object_or_404(Controller, device=device)
                associated_bridges = controller.bridges.all()
                for bridge in associated_bridges:
                    logger.debug(f"Bridge Name: {bridge.name}, Device: {bridge.device.name}")
                    bridge_name = bridge.name
                    bridge_host_device = bridge.device
                    bridge_host_lan_ip_address = bridge_host_device.lan_ip_address

                    inv_content = create_inv_data(bridge_host_lan_ip_address, bridge_host_device.username, bridge_host_device.password)
                    inv_path = create_temp_inv(inv_content)

                    delete_controller = run_playbook_with_extravars(
                        'remove-controller', playbook_dir_path, inv_path,
                        {
                            'bridge_name': bridge_name,
                            'ip_address': bridge_host_lan_ip_address,
                        }
                    )
                    # save_bridge_name_to_config(bridge_name, config_path)
                    # write_to_inventory(bridge_host_lan_ip_address, bridge_host_device.username,
                    #                    bridge_host_device.password, inventory_path)
                    # save_ip_to_config(bridge_host_lan_ip_address, config_path)
                    # delete_controller = run_playbook('remove-controller', playbook_dir_path, inventory_path)

                    if delete_controller.get('status') == 'success':
                        bridge.controller = None
                        bridge.save()
                    else:
                        return Response(
                            {'status': 'failed', 'message': 'Unable to remove controller from associated bridges'
                                                            ' due to external system failure.'},
                            status=status.HTTP_400_BAD_REQUEST)
            # delete bridges on the device
            if bridges:
                for b in bridges:
                    inv_content = create_inv_data(lan_ip_address, device.username, device.password)
                    inv_path = create_temp_inv(inv_content)

                    delete_bridge = run_playbook_with_extravars(
                        'ovs-delete-bridge', playbook_dir_path, inv_path,
                        {
                            'bridge_name': b.name,
                            'ip_address': lan_ip_address,
                        }
                    )

                    # save_bridge_name_to_config(b.name, config_path)
                    # write_to_inventory(lan_ip_address, device.username, device.password, inventory_path)
                    # save_ip_to_config(lan_ip_address, config_path)
                    # delete_bridge = run_playbook('ovs-delete-bridge', playbook_dir_path, inventory_path)
                    if delete_bridge.get('status') == 'success':
                        logger.debug(f'Bridge {b.name} successfully deleted on {device.name}')
                    else:
                        logger.debug(delete_bridge)
                        if 'Failed to connect' in delete_bridge.get('error'):
                            return Response({
                                'status': 'failed', 'message': 'Could not connect to the device. Is it online?'
                            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


# class UnassignedDevicePortsView(APIView):
#     def get(self, request, lan_ip_address):
#         try:
#             ports_data = [{'name': port.name} for port in ports]
#             device = get_object_or_404(Device, lan_ip_address=lan_ip_address)
#             ports = Port.objects.filter(bridge__device=device)
#             if ports.exists():
#                 for port in ports:
#                 ports_data = [{'name': port.name} for port in ports]
#                 return Response({'status': 'success', 'ports': ports_data})
#             else:
#                 return Response({'status': 'info', 'message': 'No ports assigned to this device.'})
#         except Exception as e:
#             return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CategoryListView(APIView):
    def get(self, request):
        try:
            # Get query parameters
            model_name = request.query_params.get('model_name')
            include_legacy = request.query_params.get('include_legacy', 'false').lower() == 'true'
            
            if model_name:
                # Get categories for a specific model
                
                try:
                    model_config = ModelConfiguration.objects.get(name=model_name)
                    categories = Category.objects.filter(model_configuration=model_config)
                    category_names = list(categories.values_list('name', flat=True))
                    
                    return JsonResponse({
                        'categories': category_names,
                        'model_name': model_name,
                        'total_categories': len(category_names)
                    }, status=200)
                except ModelConfiguration.DoesNotExist:
                    return JsonResponse({
                        'error': f'Model "{model_name}" not found'
                    }, status=404)
            else:
                # Get categories from the active model (default behavior)
                active_model_categories = model_manager.get_active_model_categories()
                
                if include_legacy:
                    # Include legacy categories (those without model_configuration)
                    legacy_categories = list(Category.objects.filter(
                        model_configuration__isnull=True
                    ).values_list('name', flat=True))
                    
                    # Combine active model categories with legacy categories
                    all_categories = list(set(active_model_categories + legacy_categories))
                    
                    return JsonResponse({
                        'categories': all_categories,
                        'active_model': model_manager.active_model,
                        'total_categories': len(all_categories),
                        'legacy_categories': legacy_categories
                    }, status=200)
                else:
                    if active_model_categories:
                        return JsonResponse({
                            'categories': active_model_categories,
                            'active_model': model_manager.active_model,
                            'total_categories': len(active_model_categories)
                        }, status=200)
                    else:
                        return JsonResponse({
                            'error': 'No active model found or no categories available',
                            'active_model': model_manager.active_model
                        }, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

# ------ CONTROLLER VIEWS -------
class ControllerViewSet(ModelViewSet):
    """
    A viewset that provides the standard actions (GET, POST, PUT, DELETE)
    for the Controller model.
    """
    queryset = Controller.objects.all()
    serializer_class = ControllerSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        # Add any custom logic when creating a Controller, if needed
        serializer.save()

    def perform_update(self, serializer):
        # Add any custom logic when updating a Controller, if needed
        serializer.save()

    @action(detail=False, methods=['get'], url_path='onos')
    def onos(self, request):
        onos_controllers = self.queryset.filter(type='onos')
        serializer = self.get_serializer(onos_controllers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='odl')
    def odl_controllers(self, request):
        odl_controllers = self.queryset.filter(type='odl').select_related('device')
        serializer = self.get_serializer(odl_controllers, many=True)  # Or a more specific serializer if needed
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='switches')
    def switches(self, request, pk=None):
        controller = self.get_object()
        switches = controller.switches.all()
        serializer = DeviceSerializer(switches, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# ----- SWITCH VIEWS ------
class SwitchViewSet(ModelViewSet):
    """
    A viewset that provides standard actions (GET, POST, PUT, DELETE)
    for switches (device_type='switch').
    """
    queryset = Device.objects.filter(device_type="switch")
    serializer_class = DeviceSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        # Ensure only switches can be created here
        serializer.save(device_type="switch")

    @action(detail=True, methods=['get'], url_path='ports')
    def ports(self, request, pk=None):
        """
        Custom action to fetch ports associated with a specific switch.
        """
        try:
            switch = self.get_object()
            ports = switch.ports.all()
            ports_data = [{'name': port.name} for port in ports]
            return Response({"ports": ports_data}, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=True, methods=['get'], url_path='bridges')
    def bridges(self, request, pk=None):
        """
        Custom action to fetch bridges associated with a specific switch.
        """
        try:
            logger.debug('Getting switch')
            switch = self.get_object()
            logger.debug('Getting switch bridges...')
            bridges = switch.bridges.all()
            logger.debug('Serializing bridges...')
            data = BridgeSerializer(bridges, many=True).data
            return Response({"bridges": data}, status=200)
        except Exception as e:
            logger.exception('Error getting switch bridges...')
            return Response({"error": str(e)}, status=500)
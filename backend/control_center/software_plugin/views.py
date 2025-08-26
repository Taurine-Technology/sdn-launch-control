# File: plugins/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Plugin, PluginRequirement, PluginInstallation, SnifferInstallationConfig
from .serializers import (
    PluginSerializer, PluginRequirementSerializer, PluginInstallationSerializer,
    SnifferInstallationConfigSerializer # Import new serializer
)
from knox.auth import TokenAuthentication
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError as DjangoValidationError # Alias to avoid clash
from rest_framework.exceptions import ValidationError as DRFValidationError # Alias for DRF validation
from general.models import Device
# Make sure install_sniffer_util is correctly imported
from utils.install_plugin import install_sniffer_util
from utils.install_plugin import uninstall_sniffer_util
from utils.install_plugin import edit_sniffer_util
import logging

from general.models import Bridge

logger = logging.getLogger(__name__)

# Define the sniffer plugin alias or name as a constant
SNIFFER_PLUGIN_ALIAS = "tau-traffic-classification-sniffer" # Or use .name if checking name field

class PluginViewSet(viewsets.ModelViewSet):
    """
    API for managing Plugins. Includes action to install sniffer.
    """
    queryset = Plugin.objects.all()
    serializer_class = PluginSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=['post'], url_path='install-sniffer')
    def install_sniffer_plugin(self, request):
        """
        Install the Sniffer Plugin, create/update the base installation record,
        and create/update the specific sniffer configuration record.
        """
        try:
            data = request.data
            lan_ip_address = data.get('lan_ip_address')
            api_base_url = data.get('api_base_url')
            monitor_interface = data.get('monitor_interface')
            port_to_client = data.get('port_to_client')
            port_to_router = data.get('port_to_router')
            bridge_name = data.get('bridge_name')

            required_fields = ['lan_ip_address', 'api_base_url', 'monitor_interface', 'port_to_client', 'port_to_router', 'bridge_name']
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return Response({"status": "error", "message": f"Missing required fields: {', '.join(missing_fields)}"},
                                status=status.HTTP_400_BAD_REQUEST)

            validate_ipv4_address(lan_ip_address)
            device = get_object_or_404(Device, lan_ip_address=lan_ip_address,device_type='switch')

            bridge = get_object_or_404(Bridge, device=device, name=bridge_name)

            if not bridge.odl_node_id:
                return Response({
                    "status": "error",
                    "message": f"Bridge '{bridge_name}' on device '{lan_ip_address}' does not have an ODL Node ID configured."
                }, status=status.HTTP_400_BAD_REQUEST)
            odl_switch_id = bridge.odl_node_id

            if not bridge.controller:
                return Response({
                    "status": "error",
                    "message": f"Bridge '{bridge_name}' on device '{lan_ip_address}' is not associated with any SDN controller."
                }, status=status.HTTP_400_BAD_REQUEST)


            sdn_controller_instance = bridge.controller
            if not sdn_controller_instance.device:  # The Device instance linked to the Controller model
                return Response({
                    "status": "error",
                    "message": f"The SDN controller '{sdn_controller_instance.id}' associated with bridge '{bridge_name}' does not have a linked device for IP."
                }, status=status.HTTP_400_BAD_REQUEST)
            controller_ip = sdn_controller_instance.device.lan_ip_address


            plugin = get_object_or_404(Plugin, name=SNIFFER_PLUGIN_ALIAS)

            # Call the installation utility function
            response = install_sniffer_util(
                lan_ip_address, api_base_url, monitor_interface,
                port_to_client, port_to_router, bridge_name,
                odl_switch_id, controller_ip
            )

            if response["status"] == "success":
                # Use atomic transaction to ensure both records are created/updated or none are
                with transaction.atomic():
                    # Step 1: Create or update the base PluginInstallation record
                    installation, created = PluginInstallation.objects.update_or_create(
                        plugin=plugin,
                        device=device,
                        # No defaults needed here unless you have other generic fields
                    )

                    # Step 2: Create or update the SnifferInstallationConfig record
                    config_data = {
                        'api_base_url': api_base_url,
                        'monitor_interface': monitor_interface,
                        'port_to_client': port_to_client,
                        'port_to_router': port_to_router,
                        'bridge_name': bridge_name,
                    }
                    # Use update_or_create with the installation instance as the primary key
                    config_instance, config_created = SnifferInstallationConfig.objects.update_or_create(
                        installation=installation, # Link to the base installation
                        defaults=config_data
                    )

                action_word = "installed" if created else "updated"
                # Return the created/updated config data using its serializer
                config_serializer = SnifferInstallationConfigSerializer(config_instance)
                return Response({
                        "status": "success",
                        "message": f"Sniffer Plugin configuration {action_word} successfully",
                        "config": config_serializer.data # Return the config details
                    }, status=status.HTTP_200_OK if created else status.HTTP_200_OK) # 201 might be better if always new config?

            else:
                logger.error(f"Sniffer installation failed for {lan_ip_address}: {response.get('message')}")
                return Response({"status": "error", "message": f"Failed to install sniffer on target device: {response.get('message')}"},
                                status=status.HTTP_400_BAD_REQUEST)

        except DjangoValidationError as e:
             # Handle potential validation errors from model's clean() method or validate_ipv4
             return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Plugin.DoesNotExist:
             return Response({"status": "error", "message": f"Plugin '{SNIFFER_PLUGIN_ALIAS}' not found"}, status=status.HTTP_404_NOT_FOUND)
        except Device.DoesNotExist:
             return Response({"status": "error", "message": "Device not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
             logger.exception(f"Unexpected error during sniffer installation: {e}")
             return Response({"status": "error", "message": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PluginRequirementViewSet(viewsets.ModelViewSet):
    """
    API for managing Plugin Dependencies.
    """
    queryset = PluginRequirement.objects.all()
    serializer_class = PluginRequirementSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


class PluginInstallationViewSet(viewsets.ModelViewSet):
    """
    API for tracking Plugin Installations on devices.
    Sniffer-specific config management is handled by SnifferInstallationConfigViewSet.
    """
    queryset = PluginInstallation.objects.all()
    serializer_class = PluginInstallationSerializer # This now includes nested sniffer_config
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    # The default list/retrieve methods will now show nested sniffer_config if available.

    # Note: The default destroy method here will delete the PluginInstallation
    # and cascade-delete the SnifferInstallationConfig, but it does NOT
    # trigger any uninstall logic on the device itself.


# --- NEW DEDICATED VIEWSET for Sniffer Config ---
class SnifferInstallationConfigViewSet(viewsets.ModelViewSet):
    """
    API specifically for managing Sniffer Plugin installation configurations.
    Provides list, retrieve, update, and delete operations for sniffer configs.
    Update triggers re-installation on the device.
    Delete triggers un-installation on the device.
    Create is disabled - use PluginViewSet's install-sniffer action instead.
    """
    queryset = SnifferInstallationConfig.objects.all()
    serializer_class = SnifferInstallationConfigSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    # Disable direct creation via this endpoint
    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Creation of sniffer config is not allowed directly. Use the '/plugins/install-sniffer/' endpoint."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    # Override update to re-run installation utility
    def update(self, request, *args, **kwargs):
        """
        Updates the Sniffer configuration and re-runs the edit utility
        on the target device with the new parameters.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object() # Gets SnifferInstallationConfig instance
        installation = instance.installation # Get the parent PluginInstallation

        if not installation.device:
             return Response({"status": "error", "message": "Cannot update sniffer config for a server-side installation."},
                            status=status.HTTP_400_BAD_REQUEST)

        lan_ip_address = installation.device.lan_ip_address

        # --- Data Extraction and Validation ---
        data = request.data
        api_base_url = data.get('api_base_url', instance.api_base_url)
        monitor_interface = data.get('monitor_interface', instance.monitor_interface)
        port_to_client = data.get('port_to_client', instance.port_to_client)
        port_to_router = data.get('port_to_router', instance.port_to_router)
        bridge_name = data.get('bridge_name', instance.bridge_name)

        # Correctly retrieve the Bridge object for this device and bridge_name
        bridge = Bridge.objects.filter(device=installation.device, name=bridge_name).first()
        odl_switch_id = bridge.odl_node_id if bridge else None
        controller_ip = bridge.controller.device.lan_ip_address if bridge and bridge.controller and bridge.controller.device else None

        required_fields = ['api_base_url', 'monitor_interface', 'port_to_client', 'port_to_router', 'bridge_name']
        if not all([api_base_url, monitor_interface, port_to_client, port_to_router, bridge_name]):
             raise DRFValidationError("Missing required fields for sniffer update.")

        logger.info(f"Attempting to update sniffer config for installation ID {installation.id} on device {lan_ip_address}")

        try:
            # --- Run Edit Utility ---
            edit_response = edit_sniffer_util(
                lan_ip_address, api_base_url, monitor_interface,
                port_to_client, port_to_router, bridge_name,
                odl_switch_id, controller_ip
            )

            if edit_response["status"] == "success":
                # --- Update DB Record on Success ---
                # Only pass updatable fields to the serializer (not installation_id)
                update_fields = ['api_base_url', 'monitor_interface', 'port_to_client', 'port_to_router', 'bridge_name']
                update_data = {field: data.get(field, getattr(instance, field)) for field in update_fields}
                serializer = self.get_serializer(instance, data=update_data, partial=partial)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer) # Saves the SnifferInstallationConfig instance

                logger.info(f"Successfully updated sniffer config for installation ID {installation.id}")
                return Response(serializer.data)
            else:
                # --- Handle Edit Failure ---
                error_msg = edit_response.get('message', 'Unknown edit error')
                logger.error(f"Sniffer edit failed for installation ID {installation.id}: {error_msg}")
                return Response(
                    {"status": "error", "message": f"Failed to update sniffer on target device: {error_msg}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
             logger.exception(f"Unexpected error during sniffer config update for installation ID {installation.id}: {e}")
             return Response({"status": "error", "message": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Override destroy to trigger uninstall (if implemented) and delete parent
    def destroy(self, request, *args, **kwargs):
        """
        Deletes the Sniffer configuration.
        Calls an uninstall utility for the device before deleting DB records.
        Deletes the parent PluginInstallation record as well.
        """
        instance = self.get_object() # Gets SnifferInstallationConfig instance
        installation = instance.installation # Get the parent PluginInstallation
        device_ip = installation.device.lan_ip_address if installation.device else None

        logger.warning(f"Attempting to delete sniffer config and installation ID {installation.id} for device {device_ip}")

        # --- Call Uninstall Utility ---
        if device_ip:
            try:
                uninstall_response = uninstall_sniffer_util(device_ip)
                if uninstall_response["status"] != "success":
                    logger.error(f"Failed to uninstall sniffer from device {device_ip}: {uninstall_response.get('message')}")
                    return Response(
                        {"status": "error", "message": f"Failed to uninstall sniffer from device: {uninstall_response.get('message')}. Database record not deleted."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                logger.info(f"Successfully uninstalled sniffer from device {device_ip}.")
            except Exception as e:
                logger.exception(f"Error during sniffer uninstall for device {device_ip}: {e}")
                return Response(
                    {"status": "error", "message": f"Error during device uninstall: {str(e)}. Database record not deleted."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            logger.info("No device associated with this sniffer installation, skipping device uninstall.")

        # --- Delete Parent Installation (will cascade delete config) ---
        try:
            installation.delete()
            logger.info(f"Successfully deleted sniffer installation ID {installation.id} and its config.")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.exception(f"Error deleting installation record ID {installation.id} from database: {e}")
            return Response(
                {"status": "error", "message": f"Failed to delete database records: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


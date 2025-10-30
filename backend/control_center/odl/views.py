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

import json
import os
import logging
import requests
import ipaddress

from django.conf import settings

from requests.auth import HTTPBasicAuth
from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import async_to_sync
from .models import Category
from network_device.models import NetworkDevice
from general.models import Device, Bridge
from .serializers import OdlMeterSerializer, OdlNodeSerializer
from channels.layers import get_channel_layer
from classifier.models import ModelConfiguration

from django.utils.timezone import now as django_now
from django.db.models import Q
from django.db import transaction
from rest_framework.decorators import api_view


from classifier.classification import create_classification_from_json
from classifier.model_manager import model_manager
from .odl_flow_utils import OdlMeterFlowRule
from .models import OdlMeter
from general.models import Controller as GeneralController
from network_data.tasks import create_flow_entries_batch

logger = logging.getLogger(__name__)

# Initialize the model manager
try:
    # The model manager will automatically load the active model
    logger.debug("Initializing model manager...")
    # Ensure the default active model is loaded
    active_model = model_manager.active_model
    if active_model:
        # Check if model is already loaded before attempting to load
        if active_model not in model_manager.loaded_models:
            success = model_manager.load_model(active_model)
            if success:
                logger.debug(f"Model manager initialized with active model: {active_model}")
            else:
                logger.error(f"Failed to load active model: {active_model}")
        else:
            logger.debug(f"Active model {active_model} already loaded")
    else:
        logger.warning("No active model configured in model manager")
        # Try to restore from database
        
        try:
            active_model_config = ModelConfiguration.objects.filter(is_active=True).first()
            if active_model_config:
                logger.debug(f"Found active model in database: {active_model_config.name}")
                state_manager.set_active_model(active_model_config.name)
                if model_manager.load_model(active_model_config.name):
                    logger.debug(f"Successfully restored active model: {active_model_config.name}")
        except Exception as db_error:
            logger.error(f"Error restoring active model from database: {db_error}")
except Exception as e:
    logger.error(f"Error initializing model manager: {e}")


class OdlMeterListView(ListAPIView):
    """
    List all ODL Meters, optionally filtered by controller_ip, switch_node_id, and model_name.
    """
    serializer_class = OdlMeterSerializer

    def get_queryset(self):
        queryset = OdlMeter.objects.all().select_related(
            'controller_device', 'network_device', 'model_configuration'
        ).prefetch_related('categories')

        controller_ip = self.request.query_params.get('controller_ip')
        switch_node_id = self.request.query_params.get('switch_node_id')
        controller_db_id = self.request.query_params.get('controller_id') # Alternative filter
        model_name = self.request.query_params.get('model_name')
        include_legacy = self.request.query_params.get('include_legacy', 'false').lower() == 'true'

        if controller_ip:
            queryset = queryset.filter(controller_device__lan_ip_address=controller_ip)
        elif controller_db_id:
            queryset = queryset.filter(controller_device__id=controller_db_id)

        if switch_node_id:
            queryset = queryset.filter(switch_node_id=switch_node_id)

        # Filter by model if specified
        if model_name:
            from classifier.models import ModelConfiguration
            try:
                model_config = ModelConfiguration.objects.get(name=model_name)
                queryset = queryset.filter(model_configuration=model_config)
            except ModelConfiguration.DoesNotExist:
                # Return empty queryset if model doesn't exist
                return OdlMeter.objects.none()
        elif not include_legacy:
            # By default, only show meters for the active model
            active_model_name = model_manager.active_model
            if active_model_name:
                from classifier.models import ModelConfiguration
                try:
                    model_config = ModelConfiguration.objects.get(name=active_model_name)
                    queryset = queryset.filter(model_configuration=model_config)
                except ModelConfiguration.DoesNotExist:
                    # If active model doesn't exist, show legacy meters (no model_configuration)
                    queryset = queryset.filter(model_configuration__isnull=True)

        return queryset.order_by('-created_at')

class CreateOpenDaylightMeterView(APIView):
    @transaction.atomic
    def post(self, request):
        try:
            data = request.data
            controller_ip = data.get('controller_ip')
            # UI sends 'switch_id', which is the ODL node-id for us
            switch_node_id_input = data.get('switch_id')

            rate_kbps = data.get('rate')

            # Optional fields from UI
            categories_data = data.get('categories', [])
            mac_address_input = data.get('mac_address', None) # UI sends 'mac_address'
            activation_period = data.get('activation_period', OdlMeter.ALL_WEEK)
            start_time_str = data.get('start_time', None)
            end_time_str = data.get('end_time', None)
            model_name = data.get('model_name', None) # Model name for model-specific meters



            if not all([controller_ip, switch_node_id_input, rate_kbps]):
                return Response(
                    {'status': 'error', 'message': 'Missing one of more required fields: controller_ip, switch_id, meter_id, rate'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                rate = int(rate_kbps)
                if rate <= 0:
                    raise ValueError("Rate and meter_id must be positive integers.")
            except ValueError as e:
                return Response(
                    {'status': 'error', 'message': f'Invalid rate or meter_id: {e}'},
                    status=status.HTTP_400_BAD_REQUEST
                )



            controller_device_obj = get_object_or_404(
                Device, lan_ip_address=controller_ip, device_type='controller'
            )

            # --- GENERATE A UNIQUE METER ID for this switch ---
            # Filter only numeric meter IDs and cast them to integers
            numeric_ids = (
                OdlMeter.objects
                .filter(
                    controller_device=controller_device_obj,
                    switch_node_id=switch_node_id_input,
                    meter_id_on_odl__regex=r'^\d+$'  # only digits
                )
                .annotate(meter_id_int=Cast('meter_id_on_odl', IntegerField()))
                .order_by('-meter_id_int')
                .values_list('meter_id_int', flat=True)
            )

            max_existing_id = numeric_ids.first() or 0
            numeric_meter_id_val = max_existing_id + 1
            numeric_meter_id_to_store_str = str(numeric_meter_id_val)

            print(f"Generated ODL Meter ID: {numeric_meter_id_val} for switch {switch_node_id_input}")
            # TODO see if ODL has a meter ID limit

            numeric_meter_id_to_store_str = str(numeric_meter_id_val)

            print(f"Generated ODL Meter ID: {numeric_meter_id_val} for switch {switch_node_id_input}")

            # --- Check 1: ODL Meter ID Uniqueness on Switch (using the generated ID) ---
            # This check is implicitly handled by the generation logic if it's robust,
            # but an explicit check after generation (before ODL call) is safer.
            if OdlMeter.objects.filter(
                    controller_device=controller_device_obj,
                    switch_node_id=switch_node_id_input,
                    meter_id_on_odl=numeric_meter_id_to_store_str  # Check with the generated string ID
            ).exists():
                # This should ideally not happen if generation logic is correct and atomic,
                # but could occur in a race condition if not careful or if IDs are manually added.
                # For now, we'll assume the simple increment is sufficient for non-highly-concurrent scenarios.
                # A more robust solution might involve retrying with a new ID or a database-level sequence.
                return Response(
                    {'status': 'error',
                     'message': f'Generated ODL Meter ID {numeric_meter_id_to_store_str} conflict for switch {switch_node_id_input}. Please try again.'},
                    status=status.HTTP_409_CONFLICT  # Or 500 if it's an internal generation issue
                )

            network_device_instance = None
            if mac_address_input:
                network_device_instance = get_object_or_404(NetworkDevice, mac_address=mac_address_input)

            # Get model configuration if model_name is provided
            model_configuration_instance = None
            if model_name:
                try:
                    from classifier.models import ModelConfiguration
                    model_configuration_instance = ModelConfiguration.objects.get(name=model_name)
                except ModelConfiguration.DoesNotExist:
                    return Response(
                        {'status': 'error', 'message': f'Model "{model_name}" not found'},
                        status=status.HTTP_400_BAD_REQUEST
                    )


            # --- Validation for Category Assignments and Time Overlaps ---
            if categories_data:  # Only if categories are being assigned
                for cat_name in categories_data:
                    try:
                        # Try to find category for the specified model first, then fallback to legacy
                        if model_configuration_instance:
                            category_obj = Category.objects.get(name=cat_name, model_configuration=model_configuration_instance)
                        else:
                            # Fallback to legacy categories (no model_configuration)
                            category_obj = Category.objects.get(name=cat_name, model_configuration__isnull=True)
                    except Category.DoesNotExist:
                        return Response(
                            {'status': 'error',
                             'message': f"Category '{cat_name}' does not exist for the specified model. Please create it first."},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # Base queryset for existing meters for this category, switch, and controller
                    existing_meters_for_category = OdlMeter.objects.filter(
                        controller_device=controller_device_obj,
                        switch_node_id=switch_node_id_input,
                        categories=category_obj
                    )

                    # Filter by user-specificity
                    if network_device_instance:
                        # If creating a user-specific meter, check against existing user-specific for that category/user.
                        # If creating a generic meter, check against existing generic for that category.
                        scoped_existing_meters = existing_meters_for_category.filter(
                            network_device=network_device_instance)
                    else:
                        # Creating a generic meter, check against existing generic meters for this category
                        scoped_existing_meters = existing_meters_for_category.filter(network_device__isnull=True)

                    # Check Rule 1 & 2 (Category Uniqueness within scope and time period)
                    # An ALL_WEEK meter for a category/scope blocks any other for that category/scope.
                    if scoped_existing_meters.filter(activation_period=OdlMeter.ALL_WEEK).exists():
                        return Response(
                            {'status': 'error',
                             'message': f"Category '{cat_name}' is already assigned to an 'ALL_WEEK' meter for this switch/user scope. Cannot add another."},
                            status=status.HTTP_409_CONFLICT
                        )

                    # If we are trying to create an ALL_WEEK meter, it conflicts if any WEEKDAY or WEEKEND exists for this category/scope.
                    if activation_period == OdlMeter.ALL_WEEK:
                        if scoped_existing_meters.filter(
                                Q(activation_period=OdlMeter.WEEKDAY) | Q(activation_period=OdlMeter.WEEKEND)).exists():
                            return Response(
                                {'status': 'error',
                                 'message': f"Cannot create an 'ALL_WEEK' meter for category '{cat_name}' as 'WEEKDAY' or 'WEEKEND' specific meters already exist for this switch/user scope."},
                                status=status.HTTP_409_CONFLICT
                            )

                    # If creating WEEKDAY, check for existing WEEKDAY. Same for WEEKEND.
                    if scoped_existing_meters.filter(activation_period=activation_period).exists():
                        # This means a meter for the same category, scope, AND exact activation_period already exists.
                        return Response(
                            {'status': 'error',
                             'message': f"Category '{cat_name}' is already assigned to a meter with the activation period '{activation_period}' for this switch/user scope."},
                            status=status.HTTP_409_CONFLICT
                        )
            # --- End Category Assignment Validation ---

            # ODL payload construction
            odl_flags_str = "meter-kbps"
            odl_meter_payload = {
                "flow-node-inventory:meter": [{
                    "meter-id": numeric_meter_id_val,
                    "meter-name": f"app-gen-meter-{numeric_meter_id_val}-rate-{rate}",
                    "flags": odl_flags_str,
                    "meter-band-headers": {
                        "meter-band-header": [{
                            "band-id": 0,
                            "drop-rate": rate,
                            "drop-burst-size": rate * 2,
                            "meter-band-types": {"flags": "ofpmbt-drop"},
                        }]
                    }
                }]
            }

            odl_api_url = f"http://{controller_ip}:8181/rests/data/opendaylight-inventory:nodes/node={switch_node_id_input}/flow-node-inventory:meter={numeric_meter_id_val}"
            print(f"Sending ODL meter creation request to: {odl_api_url}")  # For debugging
            print(f"Sending ODL meter creation payload: {json.dumps(odl_meter_payload)}")  # For debugging

            try:
                response = requests.put(
                    odl_api_url, json=odl_meter_payload, auth=HTTPBasicAuth('admin', 'admin'),
                    headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
                    timeout=20
                )
                response.raise_for_status() # Will raise an exception for 4xx/5xx errors
            except requests.exceptions.HTTPError as e:
                err_msg = f"Failed to create meter on ODL. Status: {e.response.status_code}. Response: {e.response.text}"
                print(err_msg)  # For debugging
                return Response({'status': 'error', 'message': err_msg}, status=e.response.status_code)
            except requests.exceptions.RequestException as e:
                err_msg = f"Network error communicating with ODL: {e}"
                print(err_msg)  # For debugging
                return Response({'status': 'error', 'message': err_msg}, status=status.HTTP_504_GATEWAY_TIMEOUT)

            # Create OdlMeter instance
            db_meter = OdlMeter.objects.create(
                controller_device=controller_device_obj,
                meter_id_on_odl=numeric_meter_id_to_store_str,
                meter_type='drop',
                rate=rate,
                switch_node_id=switch_node_id_input,
                odl_flags=odl_flags_str, # Store the flags used
                network_device=network_device_instance,
                model_configuration=model_configuration_instance,
                activation_period=activation_period,
                start_time=start_time_str,
                end_time=end_time_str,
            )

            if categories_data:
                for cat_name in categories_data:
                    # Use the same logic as in validation to get the correct category
                    if model_configuration_instance:
                        category = Category.objects.get(name=cat_name, model_configuration=model_configuration_instance)
                    else:
                        # Fallback to legacy categories (no model_configuration)
                        category = Category.objects.get(name=cat_name, model_configuration__isnull=True)
                    db_meter.categories.add(category)

            serializer = OdlMeterSerializer(db_meter)
            return Response(
                {'status': 'success', 'message': 'ODL Meter created successfully.', 'meter': serializer.data},
                status=status.HTTP_201_CREATED
            )

        except Device.DoesNotExist:
            return Response({'status': 'error', 'message': 'Controller Device not found.'}, status=status.HTTP_404_NOT_FOUND)
        except NetworkDevice.DoesNotExist:
            return Response({'status': 'error', 'message': 'NetworkDevice not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Unexpected error in CreateOpenDaylightMeterView: {e}")
            return Response(
                {'status': 'error', 'message': f'An unexpected server error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
def odl_classify_and_apply_policy(request):
    if request.method == 'POST':
        data = request.data
        # Accept both a single object and a list of objects
        if isinstance(data, dict):
            data_list = [data]
            single_input = True
        elif isinstance(data, list):
            data_list = data
            single_input = False
        else:
            return Response({'status': 'error', 'message': 'Invalid input format'}, status=400)

        results = []
        flow_entries_to_log = []  # Collect flow log dicts here
        for item in data_list:
            if not model_manager.get_active_model():
                results.append({
                    "status": "error",
                    "message": "No active classification model available"
                })
                continue
            port_to_router_of = item.get('port_to_router')
            port_to_client_of = item.get('port_to_client')
            odl_switch_node_id = item.get('switch_id')
            client_mac = item.get('src_mac')
            destination_mac_for_flow = item.get('dst_mac')
            client_ip = item.get('src_ip')
            dst_ip = item.get('dst_ip')
            
            # Function to check if IP is private
            def is_private_ip(ip):
                try:
                    return ipaddress.ip_address(ip).is_private
                except Exception:
                    return False
            
            # Extract public IP for ASN lookup (prefer src_ip, fallback to dst_ip)
            public_ip_for_asn = None
            if client_ip and not is_private_ip(client_ip):
                public_ip_for_asn = client_ip
            elif dst_ip and not is_private_ip(dst_ip):
                public_ip_for_asn = dst_ip
            
            # Keep existing logic for private IP (for network device creation)
            private_ip = client_ip if client_ip and is_private_ip(client_ip) else None
            if not all([port_to_router_of, port_to_client_of, odl_switch_node_id, client_mac]):
                results.append({
                    "status": "error",
                    "message": "Missing required fields: port_to_router, port_to_client, switch_id (ODL Node ID), src_mac"
                })
                continue
            try:
                classification_obj = create_classification_from_json(item)
                # Pass the public IP address to predict_flow for ASN lookup when confidence is low
                predicted_app_tuple = model_manager.predict_flow(classification_obj.payload, public_ip_for_asn)
                application_name = predicted_app_tuple[0]
                flow_data = {
                    'src_ip': item.get('src_ip'),
                    'dst_ip': item.get('dst_ip'),
                    'src_mac': item.get('src_mac'),
                    'src_port': item.get('src_port'),
                    'dst_port': item.get('dst_port'),
                    'classification': application_name,
                }
                flow_entries_to_log.append(flow_data)  # Collect for batch logging
                network_device, created = NetworkDevice.objects.get_or_create(
                    mac_address=client_mac,
                    defaults={
                        'device_type': 'end_user',
                        'ip_address': private_ip
                    }
                )
                # If the device already existed, update the IP if it's different, provided, and private
                if not created and private_ip:
                    if network_device.ip_address != private_ip:
                        network_device.ip_address = private_ip
                        network_device.save(update_fields=['ip_address'])
                flow_application_results = []
                applied_meter_id = None
                odl_controller_ip = item.get('controller_ip')
                if not odl_controller_ip:
                    results.append({
                        "status": "error",
                        "message": "controller_ip for OpenDaylight is required."
                    })
                    continue
                try:
                    controller_device_obj = Device.objects.get(lan_ip_address=odl_controller_ip, device_type='controller')
                    general_controller_profile = GeneralController.objects.get(device=controller_device_obj, type='odl')
                except Device.DoesNotExist:
                    results.append({
                        "status": "error",
                        "message": f"ODL Controller Device with IP {odl_controller_ip} not found."
                    })
                    continue
                except GeneralController.DoesNotExist:
                    results.append({
                        "status": "error",
                        "message": f"Device {odl_controller_ip} is not configured as an OpenDaylight controller."
                    })
                    continue
                try:
                    # Try to find category for the active model first
                    active_model_name = model_manager.active_model
                    if active_model_name:
                        from classifier.models import ModelConfiguration
                        try:
                            model_config = ModelConfiguration.objects.get(name=active_model_name)
                            category_obj = Category.objects.get(name=application_name, model_configuration=model_config)
                        except (ModelConfiguration.DoesNotExist, Category.DoesNotExist):
                            # Fallback to legacy categories (no model_configuration)
                            category_obj = Category.objects.get(name=application_name, model_configuration__isnull=True)
                    else:
                        # No active model, use legacy categories
                        category_obj = Category.objects.get(name=application_name, model_configuration__isnull=True)
                    
                    if not category_obj.category_cookie:
                        print(f"Category '{application_name}' found but has no pre-calculated cookie. Regenerating.")
                        category_obj.save()
                    category_cookie_to_use = category_obj.category_cookie
                except Category.DoesNotExist:
                    print(f"Category '{application_name}' not found in database. Cannot apply policy.")
                    results.append({
                        "status": "error",
                        "message": f"Category '{application_name}' not found."
                    })
                    continue
                # Build meter queryset with model-specific filtering
                meter_queryset = OdlMeter.objects.filter(
                    categories__name=application_name,
                    controller_device=controller_device_obj,
                    switch_node_id=odl_switch_node_id
                )
                
                # Filter by active model if available
                active_model_name = model_manager.active_model
                if active_model_name:
                    from classifier.models import ModelConfiguration
                    try:
                        model_config = ModelConfiguration.objects.get(name=active_model_name)
                        # First try to find meters for the active model
                        model_specific_meters = meter_queryset.filter(model_configuration=model_config)
                        if model_specific_meters.exists():
                            meter_queryset = model_specific_meters
                        else:
                            # Fallback to legacy meters (no model_configuration)
                            meter_queryset = meter_queryset.filter(model_configuration__isnull=True)
                    except ModelConfiguration.DoesNotExist:
                        # If active model doesn't exist, use legacy meters
                        meter_queryset = meter_queryset.filter(model_configuration__isnull=True)
                else:
                    # No active model, use legacy meters
                    meter_queryset = meter_queryset.filter(model_configuration__isnull=True)
                current_time = django_now().time()
                current_day_is_weekday = django_now().weekday() < 5
                active_meters = meter_queryset.filter(
                    Q(network_device=network_device) | Q(network_device__isnull=True)
                ).order_by('network_device')
                final_selected_meter = None
                for potential_meter in active_meters:
                    is_active_now = False
                    if potential_meter.activation_period == OdlMeter.ALL_WEEK:
                        is_active_now = True
                    elif potential_meter.activation_period == OdlMeter.WEEKDAY and current_day_is_weekday:
                        if not potential_meter.start_time or (
                                potential_meter.start_time <= current_time <= potential_meter.end_time): is_active_now = True
                    elif potential_meter.activation_period == OdlMeter.WEEKEND and not current_day_is_weekday:
                        if not potential_meter.start_time or (
                                potential_meter.start_time <= current_time <= potential_meter.end_time): is_active_now = True
                    if is_active_now:
                        final_selected_meter = potential_meter
                        break
                if final_selected_meter:
                    applied_meter_id = final_selected_meter.meter_id_on_odl
                    protocol_type = 'udp'
                    if classification_obj.tcp == 1:
                        protocol_type = 'tcp'
                    odl_flow_manager = OdlMeterFlowRule(
                        protocol_str=protocol_type,
                        client_port_num=classification_obj.client_port,
                        in_port_of_number_client_to_server=port_to_client_of,
                        out_port_of_number_client_to_server=port_to_router_of,
                        in_port_of_number_server_to_client=port_to_router_of,
                        out_port_of_number_server_to_client=port_to_client_of,
                        client_mac_address=client_mac,
                        server_mac_address=destination_mac_for_flow,
                        controller_ip_str=general_controller_profile.device.lan_ip_address,
                        odl_meter_id_numeric=int(final_selected_meter.meter_id_on_odl),
                        odl_switch_node_id_str=final_selected_meter.switch_node_id,
                        category_obj_cookie=category_cookie_to_use
                    )
                    flow_application_results = odl_flow_manager.apply_metered_flow_rules(controller_device_obj)
                else:
                    print(f"No active ODL Meter found for app {application_name} on switch {odl_switch_node_id} for MAC {client_mac}")
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'flow_updates',
                    {
                        'type': 'flow_message',
                        'flow': application_name
                    }
                )
                results.append({
                    'status': 'success',
                    'message': 'Classification processed.',
                    'classification': application_name,
                    'applied_meter_id': applied_meter_id,
                    'flow_results': flow_application_results
                })
            except ValueError as e:
                print(f"Invalid data for classification: {e}")
                results.append({"status": "error", "message": str(e)})
            except Exception as e:
                logger.error(f"[ODL_CLASSIFY_AND_APPLY_POLICY] Error during ODL classification/policy application: {e}")
                results.append({"status": "error", "message": f"An internal error occurred: {str(e)}"})
        # After the loop, batch log the flow entries
        if flow_entries_to_log:
            logger.debug(f"[ODL_CLASSIFY_AND_APPLY_POLICY] Batching {len(flow_entries_to_log)} flow entries")
            create_flow_entries_batch.delay(flow_entries_to_log)
        # Return a list if input was a list, or a single result if input was a dict
        if single_input:
            return Response(results[0], status=status.HTTP_200_OK if results[0].get('status') == 'success' else 400)
        else:
            return Response(results, status=status.HTTP_200_OK)


class OdlMeterDetailView(APIView):
    """
    Retrieve, update or delete an OdlMeter instance.
    """

    def get_object(self, pk):
        return get_object_or_404(OdlMeter, pk=pk)

    def get(self, request, pk, format=None):
        meter = self.get_object(pk)
        serializer = OdlMeterSerializer(meter)
        return Response(serializer.data)

    @transaction.atomic
    def put(self, request, pk, format=None):
        existing_meter = self.get_object(pk)
        data = request.data

        try:
            # --- 1. Parse and Validate Basic Inputs ---
            requested_controller_ip = data.get('controller_ip')
            requested_switch_node_id = data.get('switch_id')
            requested_meter_id_on_odl_str = str(data.get('meter_id')) # ODL numeric ID
            requested_rate_kbps_str = data.get('rate')

            requested_categories_data = data.get('categories', []) # List of category names
            requested_mac_address = data.get('mac_address', None)
            requested_activation_period = data.get('activation_period', OdlMeter.ALL_WEEK)
            requested_start_time_str = data.get('start_time', None)
            requested_end_time_str = data.get('end_time', None)

            if not all([requested_controller_ip, requested_switch_node_id, requested_meter_id_on_odl_str, requested_rate_kbps_str]):
                return Response(
                    {'status': 'error', 'message': 'Missing one or more required fields: controller_ip, switch_id, meter_id, rate'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                requested_rate_val = int(requested_rate_kbps_str)
                requested_meter_id_on_odl_int = int(requested_meter_id_on_odl_str)
                if requested_rate_val <= 0 or requested_meter_id_on_odl_int <= 0:
                    raise ValueError("Rate and meter_id must be positive integers.")
            except ValueError as e:
                return Response(
                    {'status': 'error', 'message': f'Invalid rate or meter_id: {e}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            requested_controller_device_obj = get_object_or_404(
                Device, lan_ip_address=requested_controller_ip, device_type='controller'
            )

            requested_network_device_instance = None
            if requested_mac_address:
                requested_network_device_instance = get_object_or_404(NetworkDevice, mac_address=requested_mac_address)

            # --- 2. Validation: ODL Meter Uniqueness for the target configuration ---
            # Check if the target ODL meter configuration (controller, switch, meter_id)
            # is already used by *another* local OdlMeter entry.
            potential_db_conflict = OdlMeter.objects.filter(
                controller_device=requested_controller_device_obj,
                switch_node_id=requested_switch_node_id,
                meter_id_on_odl=requested_meter_id_on_odl_str
            ).exclude(pk=existing_meter.pk) # Exclude the current meter instance

            if potential_db_conflict.exists():
                return Response(
                    {'status': 'error', 'message': f'The ODL meter configuration (Controller: {requested_controller_ip}, Switch: {requested_switch_node_id}, Meter ID: {requested_meter_id_on_odl_str}) is already assigned to another meter in the database.'},
                    status=status.HTTP_409_CONFLICT
                )

            # --- 3. Validation: Category Assignments and Time Overlaps ---
            # This validation uses the *requested* controller, switch, and categories.
            if requested_categories_data:
                for cat_name in requested_categories_data:
                    try:
                        # Try to find category for the existing meter's model first, then fallback to legacy
                        if existing_meter.model_configuration:
                            category_obj = Category.objects.get(name=cat_name, model_configuration=existing_meter.model_configuration)
                        else:
                            # Fallback to legacy categories (no model_configuration)
                            category_obj = Category.objects.get(name=cat_name, model_configuration__isnull=True)
                    except Category.DoesNotExist:
                        return Response(
                            {'status': 'error', 'message': f"Category '{cat_name}' does not exist for the meter's model. Please create it first."},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # Base queryset for existing meters for this category on the target switch/controller, excluding self
                    existing_meters_for_category_check = OdlMeter.objects.filter(
                        controller_device=requested_controller_device_obj,
                        switch_node_id=requested_switch_node_id,
                        categories=category_obj
                    ).exclude(pk=existing_meter.pk)

                    # Filter by user-specificity for the check
                    if requested_network_device_instance:
                        scoped_existing_meters_check = existing_meters_for_category_check.filter(
                            network_device=requested_network_device_instance)
                    else:
                        scoped_existing_meters_check = existing_meters_for_category_check.filter(network_device__isnull=True)

                    # Rule checks (same as create, but against `scoped_existing_meters_check`)
                    if scoped_existing_meters_check.filter(activation_period=OdlMeter.ALL_WEEK).exists():
                        return Response(
                            {'status': 'error', 'message': f"Category '{cat_name}' is already assigned to an 'ALL_WEEK' meter for the target switch/user scope. Cannot update."},
                            status=status.HTTP_409_CONFLICT
                        )
                    if requested_activation_period == OdlMeter.ALL_WEEK:
                        if scoped_existing_meters_check.filter(
                                Q(activation_period=OdlMeter.WEEKDAY) | Q(activation_period=OdlMeter.WEEKEND)).exists():
                            return Response(
                                {'status': 'error', 'message': f"Cannot set 'ALL_WEEK' for category '{cat_name}' as 'WEEKDAY' or 'WEEKEND' specific meters already exist for the target switch/user scope."},
                                status=status.HTTP_409_CONFLICT
                            )
                    if scoped_existing_meters_check.filter(activation_period=requested_activation_period).exists():
                        return Response(
                            {'status': 'error', 'message': f"Category '{cat_name}' is already assigned to a meter with the activation period '{requested_activation_period}' for the target switch/user scope."},
                            status=status.HTTP_409_CONFLICT
                        )

            # --- 4. Determine if ODL Configuration Needs Update/Creation ---
            odl_config_has_changed = False
            if (existing_meter.controller_device.pk != requested_controller_device_obj.pk or
                existing_meter.switch_node_id != requested_switch_node_id or
                existing_meter.meter_id_on_odl != requested_meter_id_on_odl_str or
                existing_meter.rate != requested_rate_val):
                odl_config_has_changed = True

            if odl_config_has_changed:
                # ODL payload construction for the new/updated configuration
                odl_flags_str = "meter-kbps"
                odl_meter_payload = {
                    "flow-node-inventory:meter": [{
                        "meter-id": requested_meter_id_on_odl_int,
                        "meter-name": f"app-gen-meter-{requested_meter_id_on_odl_int}-rate-{requested_rate_val}",
                        "flags": odl_flags_str,
                        "meter-band-headers": {
                            "meter-band-header": [{
                                "band-id": 0,
                                "drop-rate": requested_rate_val,
                                "drop-burst-size": requested_rate_val * 2,
                                "meter-band-types": {"flags": "ofpmbt-drop"},
                            }]
                        }
                    }]
                }
                odl_api_url = f"http://{requested_controller_ip}:8181/rests/data/opendaylight-inventory:nodes/node={requested_switch_node_id}/flow-node-inventory:meter={requested_meter_id_on_odl_int}"
                print(f"Sending ODL meter PUT request to: {odl_api_url}")
                print(f"Sending ODL meter PUT payload: {json.dumps(odl_meter_payload)}")

                try:
                    response = requests.put(
                        odl_api_url, json=odl_meter_payload, auth=HTTPBasicAuth('admin', 'admin'),
                        headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
                        timeout=20
                    )
                    response.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    err_msg = f"Failed to update/create meter on ODL. Status: {e.response.status_code}. Response: {e.response.text}"
                    print(err_msg)
                    return Response({'status': 'error', 'message': err_msg}, status=e.response.status_code)
                except requests.exceptions.RequestException as e:
                    err_msg = f"Network error communicating with ODL: {e}"
                    print(err_msg)
                    return Response({'status': 'error', 'message': err_msg}, status=status.HTTP_504_GATEWAY_TIMEOUT)

            # --- 5. Update Database Instance ---
            existing_meter.controller_device = requested_controller_device_obj
            existing_meter.switch_node_id = requested_switch_node_id
            existing_meter.meter_id_on_odl = requested_meter_id_on_odl_str
            existing_meter.rate = requested_rate_val
            existing_meter.meter_type = 'drop'
            existing_meter.odl_flags = "meter-kbps"

            existing_meter.network_device = requested_network_device_instance
            existing_meter.activation_period = requested_activation_period
            existing_meter.start_time = requested_start_time_str if requested_start_time_str else None
            existing_meter.end_time = requested_end_time_str if requested_end_time_str else None

            # Update categories
            updated_categories = []
            if requested_categories_data:
                for cat_name in requested_categories_data:
                    # Use the same logic as in validation to get the correct category
                    if existing_meter.model_configuration:
                        category = Category.objects.get(name=cat_name, model_configuration=existing_meter.model_configuration)
                    else:
                        # Fallback to legacy categories (no model_configuration)
                        category = Category.objects.get(name=cat_name, model_configuration__isnull=True)
                    updated_categories.append(category)
            existing_meter.categories.set(updated_categories)

            existing_meter.save()
            serializer = OdlMeterSerializer(existing_meter)
            return Response(
                {'status': 'success', 'message': 'ODL Meter updated successfully.', 'meter': serializer.data},
                status=status.HTTP_200_OK
            )

        except Device.DoesNotExist:
            return Response({'status': 'error', 'message': 'Target Controller Device not found.'}, status=status.HTTP_404_NOT_FOUND)
        except NetworkDevice.DoesNotExist:
            return Response({'status': 'error', 'message': 'Target NetworkDevice not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Unexpected error in OdlMeterDetailView PUT: {e}") # Log the full error
            import traceback
            traceback.print_exc() # Print stack trace for debugging
            return Response(
                {'status': 'error', 'message': f'An unexpected server error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @transaction.atomic
    def delete(self, request, pk, format=None):
        meter = self.get_object(pk)
        meter_id_on_odl = meter.meter_id_on_odl
        switch_node_id = meter.switch_node_id
        controller_ip_address = meter.controller_device.lan_ip_address

        odl_api_url = f"http://{controller_ip_address}:8181/rests/data/opendaylight-inventory:nodes/node={switch_node_id}/flow-node-inventory:meter={meter_id_on_odl}"
        try:
            response = requests.delete(
                odl_api_url,auth=HTTPBasicAuth('admin', 'admin'),
                headers={'Content-Type': 'application/xml', 'Accept': 'application/xml'},
                timeout=20
            )
            response.raise_for_status()  # Will raise an exception for 4xx/5xx errors
        except requests.exceptions.HTTPError as e:
            err_msg = f"Failed to create meter on ODL. Status: {e.response.status_code}. Response: {e.response.text}"
            print(err_msg)  # For debugging
            return Response({'status': 'error', 'message': err_msg}, status=e.response.status_code)
        except requests.exceptions.RequestException as e:
            err_msg = f"Network error communicating with ODL: {e}"
            print(err_msg)  # For debugging
            return Response({'status': 'error', 'message': err_msg}, status=status.HTTP_504_GATEWAY_TIMEOUT)
        meter.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class OdlControllerNodesView(ListAPIView):
    """
    List all ODL-controlled "nodes" (Bridges with odl_node_id)
    for a given ODL Controller.
    The controller is identified by its database ID passed in the URL.
    """
    serializer_class = OdlNodeSerializer

    def get_queryset(self):
        controller_id = self.kwargs.get('controller_id')
        if not controller_id:
            return Bridge.objects.none()

        try:
            odl_controller_profile = GeneralController.objects.get(
                pk=controller_id,
                type='odl' # Ensure it's an ODL type controller
            )
            controller_device = odl_controller_profile.device
        except GeneralController.DoesNotExist:
            return Bridge.objects.none() # Or raise a 404

        # Find bridges managed by this ODL controller that have an odl_node_id
        # The Bridge model's 'controller' FK points to general.models.Controller
        queryset = Bridge.objects.filter(
            controller=odl_controller_profile,
            odl_node_id__isnull=False
        ).exclude(odl_node_id__exact='').select_related('device').order_by('device__name', 'name')

        return queryset

class ModelManagementView(APIView):
    """
    API endpoints for managing classification models
    """
    
    def get(self, request):
        """
        List all available models and their status
        """
        try:
            models_info = model_manager.list_models()
            return Response({
                'status': 'success',
                'models': models_info,
                'active_model': model_manager.active_model
            })
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return Response({
                'status': 'error',
                'message': f'Error listing models: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """
        Set the active model for classification
        """
        try:
            model_name = request.data.get('model_name')
            if not model_name:
                return Response({
                    'status': 'error',
                    'message': 'model_name is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            success = model_manager.set_active_model(model_name)
            if success:
                return Response({
                    'status': 'success',
                    'message': f'Active model set to: {model_name}',
                    'active_model': model_manager.active_model
                })
            else:
                return Response({
                    'status': 'error',
                    'message': f'Failed to set active model: {model_name}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error setting active model: {e}")
            return Response({
                'status': 'error',
                'message': f'Error setting active model: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ModelLoadView(APIView):
    """
    API endpoints for loading/unloading models
    """
    
    def post(self, request):
        """
        Load a specific model into memory
        """
        try:
            model_name = request.data.get('model_name')
            if not model_name:
                return Response({
                    'status': 'error',
                    'message': 'model_name is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            success = model_manager.load_model(model_name)
            if success:
                return Response({
                    'status': 'success',
                    'message': f'Model loaded: {model_name}'
                })
            else:
                return Response({
                    'status': 'error',
                    'message': f'Failed to load model: {model_name}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return Response({
                'status': 'error',
                'message': f'Error loading model: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        """
        Unload a specific model from memory
        """
        try:
            model_name = request.data.get('model_name')
            if not model_name:
                return Response({
                    'status': 'error',
                    'message': 'model_name is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            success = model_manager.unload_model(model_name)
            if success:
                return Response({
                    'status': 'success',
                    'message': f'Model unloaded: {model_name}'
                })
            else:
                return Response({
                    'status': 'error',
                    'message': f'Failed to unload model: {model_name}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error unloading model: {e}")
            return Response({
                'status': 'error',
                'message': f'Error unloading model: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ModelInfoView(APIView):
    """
    API endpoint to get detailed information about available models
    """
    
    def get(self, request):
        """
        Get detailed information about all available models
        """
        try:
            models_info = model_manager.list_models()
            
            # Add additional information for each model
            for model_info in models_info:
                # Get categories for this model
                model_categories = model_manager.get_model_categories(model_info['name'])
                model_info['categories'] = model_categories
                model_info['category_count'] = len(model_categories)
                
                # Check if model has associated meters
                from odl.models import OdlMeter
                meter_count = OdlMeter.objects.filter(
                    model_configuration__name=model_info['name']
                ).count()
                model_info['meter_count'] = meter_count
            
            return Response({
                'status': 'success',
                'models': models_info,
                'active_model': model_manager.active_model,
                'total_models': len(models_info)
            })
        except Exception as e:
            logger.error(f"Error getting model information: {e}")
            return Response({
                'status': 'error',
                'message': f'Error getting model information: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
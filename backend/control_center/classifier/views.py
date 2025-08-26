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

from django.utils.timezone import now
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework import status
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import csrf_exempt
import json
from classifier.classification import create_classification_from_json
from classifier.meter_flow_rule import MeterFlowRule
from classifier.model_manager import model_manager
from general.models import Controller, Device
from software_plugin.models import PluginInstallation, Plugin
from onos.models import Category, Meter
import os
from network_data.tasks import create_flow_entry
from network_device.models import NetworkDevice
from network_data.tasks import create_flow_entries_batch
import logging
import ipaddress

logger = logging.getLogger(__name__)
# Extract public IP for ASN lookup
                
def is_private_ip(ip):
    try:
        return ipaddress.ip_address(ip).is_private
    except Exception:
        return False



@csrf_exempt
@api_view(['POST'])
def post_flow_classification(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'flow_updates',
            {
                'type': 'flow_message',
                'flow': data
            }
        )
        return JsonResponse({'message': 'received'}, status=status.HTTP_200_OK)


@csrf_exempt
def classify(request):
    if request.method == 'POST':
        # Accept both a single object and a list of objects
        try:
            data = json.loads(request.body)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Invalid JSON: {e}'}, status=400)

        # Always work with a list
        if isinstance(data, dict):
            data_list = [data]
        elif isinstance(data, list):
            data_list = data
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid input format'}, status=400)

        results = []
        flow_entries_to_log = []
        for item in data_list:
            try:
                port_to_router = item.get('port_to_router')
                port_to_client = item.get('port_to_client')
                meter_plugin = Plugin.objects.get(name='tau-onos-metre-traffic-classification')
                meter_plugin_installed = PluginInstallation.objects.filter(plugin=meter_plugin).exists()
                model_name = item.get('model_name')
                switch_ip = item.get('lan_ip_address')
                classification = create_classification_from_json(item)
                
                # Check if we have an active model
                if not model_manager.get_active_model():
                    results.append({
                        "status": "error",
                        "message": "No active classification model available"
                    })
                    continue
                
                
                
                client_ip = item.get('src_ip')
                dst_ip = item.get('dst_ip')
                public_ip_for_asn = None
                if client_ip and not is_private_ip(client_ip):
                    public_ip_for_asn = client_ip
                elif dst_ip and not is_private_ip(dst_ip):
                    public_ip_for_asn = dst_ip
                
                # Use model_manager for prediction
                predicted_app_tuple = model_manager.predict_flow(classification.payload, public_ip_for_asn)
                application = predicted_app_tuple[0]
                flow_data = {
                    'src_ip': item.get('src_ip'),
                    'dst_ip': item.get('dst_ip'),
                    'src_mac': item.get('src_mac'),
                    'dst_mac': item.get('dst_mac'),
                    'src_port': item.get('src_port'),
                    'dst_port': item.get('dst_port'),
                    'classification': application,
                }
                flow_entries_to_log.append(flow_data)
                exists = NetworkDevice.objects.filter(mac_address=item.get('src_mac')).exists()
                if not exists:
                    NetworkDevice.objects.create(mac_address=item.get('src_mac'), device_type='end_user').save()
                flow_results = []
                if meter_plugin_installed:
                    switch_device = Device.objects.get(lan_ip_address=switch_ip, device_type='switch')
                    controller = Controller.objects.get(switches=switch_device, type='onos')
                    if Meter.objects.filter(categories__name=application, controller_device=controller.device).exists():
                        current_time = now().time()
                        current_day = now().weekday()
                        matching_meters = Meter.objects.filter(
                            categories__name=application,
                            controller_device=controller.device
                        )
                        valid_meters = matching_meters
                        src_mac = item.get('src_mac')
                        if matching_meters.filter(network_device__mac_address=src_mac).exists():
                            valid_meters = valid_meters.filter(network_device__mac_address=src_mac)
                        if current_day < 5:
                            weekday_meters = matching_meters.filter(
                                Q(activation_period="weekday") & Q(start_time__lte=current_time) & Q(end_time__gte=current_time)
                            )
                            valid_meters = valid_meters | weekday_meters if weekday_meters.exists() else valid_meters
                        else:
                            weekend_meters = matching_meters.filter(
                                Q(activation_period="weekend") & Q(start_time__lte=current_time) & Q(end_time__gte=current_time)
                            )
                            valid_meters = valid_meters | weekend_meters if weekend_meters.exists() else valid_meters
                        if valid_meters.exists():
                            meter = valid_meters.first()
                            proto = 'udp'
                            if item.get('tcp') == 1:
                                proto = 'tcp'
                            flow_rule = MeterFlowRule(
                                proto=proto,
                                client_port=classification.client_port,
                                inbound_port_src=port_to_client,
                                outbound_port_src=port_to_router,
                                inbound_port_dst=port_to_router,
                                outbound_port_dst=port_to_client,
                                category=application,
                                src_mac=classification.src_mac,
                                dst_mac=item.get('dst_mac'),
                                controller_ip=meter.controller_device.lan_ip_address,
                                meter_id=meter.meter_id,
                                switch_id=meter.switch_id
                            )
                            flow_results = flow_rule.make_flow_adjustment()
                results.append({
                    'status': 'success',
                    'classification': application,
                    'flow_results': flow_results
                })
            except Exception as e:
                results.append({'status': 'error', 'message': str(e)})
        # Batch log the flow entries
        logger.info(f"[CLASSIFIER] Batching {len(flow_entries_to_log)} flow entries")
        create_flow_entries_batch.delay(flow_entries_to_log)
        return JsonResponse(results, safe=False, status=200)


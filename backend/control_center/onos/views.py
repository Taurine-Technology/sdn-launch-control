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

import time
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework.decorators import api_view
import requests
from requests.auth import HTTPBasicAuth
import urllib.parse
from rest_framework.response import Response
from rest_framework import status
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError
from .models import Meter, Category
from general.models import Device
from .serializers import MeterSerializer
from network_device.models import NetworkDevice
from utils.meter import convert_onos_meter_api_id_to_internal_id


class MeterListView(APIView):
    def get(self, request, lan_ip_address):
        try:
            validate_ipv4_address(lan_ip_address)
            url = f"http://{lan_ip_address}:8181/onos/v1/meters/"
            meters_per_device = {}
            # Make API call
            response = requests.get(
                url=url,
                auth=HTTPBasicAuth('onos', 'rocks')
            )
            url_devices = f"http://{lan_ip_address}:8181/onos/v1/devices"
            response_devices = requests.get(
                url=url_devices,
                auth=HTTPBasicAuth('onos', 'rocks')
            )
            device_response_json = response_devices.json()
            devices = device_response_json.get('devices')
            meters = []
            for meter in response.json().get('meters'):
                band_details = meter.get('bands')[0]
                band_type = band_details.get('type')
                switch_ip = '0.0.0.0'
                for device in devices:
                    annotations = device.get('annotations')
                    device_id = device.get('id')
                    if device_id == meter.get('deviceId'):
                        switch_ip = annotations.get('managementAddress')

                if band_type == 'DROP':
                    rate = band_details.get('rate')
                    device_id = meter.get('deviceId')

                    m_id = meter.get('id')
                    state = meter.get('state')
                    unit = meter.get('unit')
                    if unit == 'KB_PER_SEC':
                        unit = 'kbs'
                    d = Device.objects.get(lan_ip_address=lan_ip_address)
                    meter_model, created = Meter.objects.get_or_create(
                        controller_device=d,
                        meter_id=m_id,
                        meter_type='drop',
                        rate=rate,
                        switch_id=device_id
                    )
                    categories = None
                    if not created:
                        categories = meter_model.categories
                    if categories:
                        m = {
                            'id': m_id,
                            'type': 'drop',
                            'ip': switch_ip,
                            'rate': f'{rate}',
                            'unit': f'{unit}',
                            'device_id': f'{device_id}',
                            'state': f'{state}',
                            'categories': f'{categories}',
                            'database_meter_id': meter.id,
                        }
                    else:
                        m = {
                            'id': m_id,
                            'type': 'drop',
                            'ip': switch_ip,
                            'rate': f'{rate}',
                            'unit': f'{unit}',
                            'device_id': f'{device_id}',
                            'state': f'{state}',
                            'categories': 'None',
                            'database_meter_id': meter.id,
                        }

                    if switch_ip in meters_per_device:
                        meters_per_device[switch_ip].append(m)
                    else:
                        meters_per_device[switch_ip] = [m]
                    meters.append(m)
            # print('XXX meters:', meters_per_device)
            return Response({"status": "success", "meters": meters}, status=status.HTTP_200_OK)
        except ValidationError:
            return Response({"status": "error", "message": "Invalid IP address format."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print('CAUGHT AN UNEXPECTED ERROR')
            print(e)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MeterListByIdView(APIView):
    def get(self, request, lan_ip_address, id):
        try:
            validate_ipv4_address(lan_ip_address)
            url = f"http://{lan_ip_address}:8181/onos/v1/meters/"
            meters_per_device = {}
            # Make API call
            response = requests.get(
                url=url,
                auth=HTTPBasicAuth('onos', 'rocks')
            )

            url_devices = f"http://{lan_ip_address}:8181/onos/v1/devices"
            response_devices = requests.get(
                url=url_devices,
                auth=HTTPBasicAuth('onos', 'rocks')
            )
            device_response_json = response_devices.json()
            devices = device_response_json.get('devices')

            meters = []
            for meter in response.json().get('meters'):
                band_details = meter.get('bands')[0]
                band_type = band_details.get('type')
                switch_ip = '0.0.0.0'
                for device in devices:
                    annotations = device.get('annotations')
                    device_id = device.get('id')
                    if device_id == meter.get('deviceId'):
                        switch_ip = annotations.get('managementAddress')

                if band_type == 'DROP':
                    rate = band_details.get('rate')
                    device_id = meter.get('deviceId')

                    m_id = meter.get('id')
                    state = meter.get('state')
                    unit = meter.get('unit')
                    if unit == 'KB_PER_SEC':
                        unit = 'kbs'

                    d = Device.objects.get(lan_ip_address=lan_ip_address)

                    try:
                        meter_models = Meter.objects.filter(
                            controller_device=d,
                            meter_id=m_id,
                            meter_type='drop',
                            rate=rate,
                            switch_id=device_id,
                        )
                        for meter_model in meter_models:
                            m = {
                                'id': meter_model.meter_id,
                                'type': meter_model.meter_type,
                                'ip': switch_ip,
                                'rate': f'{meter_model.rate}',
                                'unit': f'{unit}',
                                'device_id': f'{meter_model.switch_id}',
                                'state': f'{state}',
                                'categories': list(meter_model.categories.values_list('name', flat=True))
                                if meter_model.categories.exists() else [],
                                'network_device_mac': meter_model.network_device.mac_address if meter_model.network_device else None,
                                'activation_period': meter_model.activation_period,
                                'start_time': meter_model.start_time.strftime(
                                    "%H:%M") if meter_model.start_time else None,
                                'end_time': meter_model.end_time.strftime("%H:%M") if meter_model.end_time else None,
                                'database_meter_id': meter_model.id,
                            }
                            meters.append(m)
                            # print('Found meter:', m)
                    except Exception:
                        continue
            return Response({"status": "success", "meters": meters}, status=status.HTTP_200_OK)
        except ValidationError:
            return Response({"status": "error", "message": "Invalid IP address format."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print('CAUGHT AN UNEXPECTED ERROR')
            print(e)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateMeterView(APIView):
    def post(self, request):
        try:
            data = request.data
            controller_ip = data.get('controller_ip')
            switch_id = data.get('switch_id')
            rate = data.get('rate')
            categories = data.get('categories', [])
            mac_address = data.get('mac_address', None)
            activation_period = data.get('activation_period', 'all_week')
            start_time = data.get('start_time', None)
            end_time = data.get('end_time', None)

            # --- Basic Input Validation ---
            if not controller_ip or not switch_id or not rate:
                 return JsonResponse({'error': 'Missing required fields: controller_ip, switch_id, rate'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                rate = int(rate) # Ensure rate is an integer
            except ValueError:
                 return JsonResponse({'error': 'Rate must be a valid integer.'}, status=status.HTTP_400_BAD_REQUEST)
            # --- End Validation ---

            d = Device.objects.get(lan_ip_address=controller_ip)

            network_device = None
            if mac_address:
                try:
                    network_device = NetworkDevice.objects.get(mac_address=mac_address)
                except NetworkDevice.DoesNotExist:
                    return JsonResponse({'error': 'Network device not found with this MAC address'},
                                        status=status.HTTP_404_NOT_FOUND)

            # --- Category Assignment Check ---
            # Build the base queryset
            meters_queryset = Meter.objects.filter(switch_id=switch_id, controller_device=d)
            if network_device: # Filter further if network_device is specified
                meters_queryset = meters_queryset.filter(network_device=network_device)

            # Check if any of the *new* categories conflict with existing ones for the filtered meters
            if categories: # Only check if new categories are provided
                existing_categories_qs = Category.objects.filter(meter__in=meters_queryset).values_list('name', flat=True)
                existing_categories = set(existing_categories_qs)

                new_categories_set = set(categories)
                conflicting_categories = existing_categories.intersection(new_categories_set)

                if conflicting_categories:
                    return JsonResponse({
                        'error': f'Categories {list(conflicting_categories)} are already assigned to another meter for this switch/device combination.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            # --- End Category Check ---


            print('### STARTING METER CREATION ###')
            device_id_encoded = urllib.parse.quote(switch_id, safe='')
            url = f"http://{controller_ip}:8181/onos/v1/meters/{device_id_encoded}"
            print('url:', url)
            payload = {
                "deviceId": switch_id,
                "unit": "KB_PER_SEC",
                "burst": False,
                "bands": [
                    {
                        "type": "DROP",
                        "rate": rate,
                        # Consider making burstSize and prec configurable if needed
                        "burstSize": "0",
                        "prec": "0"
                    }
                ]
            }
            print('payload:', payload)

            # --- Send POST request to ONOS ---
            response = requests.post(
                url=url,
                json=payload,
                headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
                auth=HTTPBasicAuth('onos', 'rocks'),
                timeout=15 # Add a timeout to the request itself
            )

            print('Status code:', response.status_code)
            print('######')

            if response.status_code == 201:
                # --- !!! ADDED PAUSE HERE !!! ---
                print(f"Meter creation request sent successfully. Waiting 20 seconds for ONOS to process...")
                time.sleep(20)
                print("Wait finished. Fetching meter details...")
                # --- !!! END PAUSE !!! ---

                # --- Fetch meters again to find the new one ---
                url_meters = f"http://{controller_ip}:8181/onos/v1/meters/{device_id_encoded}"
                try:
                    response_meters = requests.get(
                        url=url_meters,
                        auth=HTTPBasicAuth('onos', 'rocks'),
                        timeout=10 # Add timeout
                    )
                    response_meters.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
                except requests.exceptions.RequestException as e:
                     print(f"Error fetching meters after creation: {e}")
                     # Decide how to handle: maybe still create DB entry with meter_id=0 or return error?
                     # For now, return error as we can't confirm the ONOS ID.
                     return JsonResponse({'error': f'Meter created on ONOS, but failed to retrieve details: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


                best_meter = None
                min_life = float('inf') # Initialize with infinity

                # Safely get meters list, default to empty list if key missing or not a list
                meters_list = response_meters.json().get('meters', [])
                if not isinstance(meters_list, list):
                    print("Warning: 'meters' key in ONOS response is not a list.")
                    meters_list = []

                for meter_json in meters_list:
                    # Add checks for existence of keys before accessing
                    device_id_meter_rsp = meter_json.get('deviceId')
                    bands = meter_json.get('bands')
                    if not device_id_meter_rsp or not bands or not isinstance(bands, list) or len(bands) == 0:
                        continue # Skip malformed meter entries

                    band = bands[0]
                    rate_rsp = band.get('rate')
                    type_rsp = band.get('type')

                    # Ensure rate_rsp is valid before comparison
                    try:
                        rate_rsp_int = int(rate_rsp)
                    except (ValueError, TypeError):
                        continue # Skip if rate is not a valid integer

                    # Only consider meters that match the conditions
                    if device_id_meter_rsp == switch_id and rate_rsp_int == rate and type_rsp == 'DROP':
                        meter_life = meter_json.get('life', float('inf')) # Default to infinity if 'life' is missing
                        # Ensure meter_life is a number
                        if isinstance(meter_life, (int, float)) and meter_life < min_life:
                            min_life = meter_life
                            best_meter = meter_json

                # --- Save Meter to Database ---
                if best_meter:
                    meter_id = best_meter.get('id')
                    print(f"Found best matching meter with ID: {meter_id} and life: {min_life}")
                else:
                    # Handle case where no matching meter was found after waiting
                    print("Warning: No matching meter found in ONOS response after waiting.")

                    return JsonResponse({'error': 'Meter created on ONOS, but could not be identified in the response after waiting.'}, status=status.HTTP_404_NOT_FOUND)


                meter = Meter(
                    controller_device=d,
                    meter_id=meter_id, # Can be None or 0 if not found
                    meter_type='drop',
                    rate=rate,
                    switch_id=switch_id,
                    network_device=network_device,
                    activation_period=activation_period,
                    start_time=start_time,
                    end_time=end_time,
                )
                meter.save()

                # Add categories if provided
                if categories:
                    for cat_name in categories:
                        category, _ = Category.objects.get_or_create(name=cat_name)
                        meter.categories.add(category)

                return JsonResponse({'message': 'Successfully created meter record (check ONOS ID if warning occurred).'}, status=status.HTTP_201_CREATED)
            else:
                # Handle non-201 status codes from the initial POST
                error_msg = f"Failed to create meter on ONOS server. Status: {response.status_code}"
                try:
                    onos_error = response.json() # Try to get error details from ONOS
                    error_msg += f", Response: {onos_error}"
                except ValueError: # Handle cases where response is not JSON
                    error_msg += f", Response: {response.text}"
                print(error_msg)
                return JsonResponse({'error': error_msg}, status=response.status_code)

        except Device.DoesNotExist:
            return JsonResponse({'error': 'Controller Device not found in database'}, status=status.HTTP_404_NOT_FOUND)
        except requests.exceptions.RequestException as e:
             # Handle network errors during requests (timeout, connection error)
             print(f"Network error communicating with ONOS: {e}")
             return JsonResponse({'error': f'Network error communicating with ONOS: {e}'}, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except Exception as e:
            print(f'CAUGHT AN UNEXPECTED ERROR: {type(e).__name__} - {e}')

            return JsonResponse({'error': f'An unexpected server error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class SwitchList(APIView):
    def get(self, request, controller_ip):
        try:
            url = f"http://{controller_ip}:8181/onos/v1/devices"
            response = requests.get(
                url=url,
                auth=HTTPBasicAuth('onos', 'rocks')
            )
            response_json = response.json()
            devices = response_json.get('devices', [])
            # Filter to only include available switches.
            available_switches = [
                device for device in devices
                if device.get("available") and device.get("type") == "SWITCH"
            ]
            return JsonResponse({'devices': available_switches}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status': 'error', 'message': f'Unknown error, please wait and try again in a bit... Error details: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def update_meter(request):
    try:
        meter_id = request.data.get('meter_id')
        categories = request.data.get('categories', '')
        controller_ip = request.data.get('controller_ip')
        mac_address = request.data.get('mac_address')
        if categories:
            categories = categories.split(',')

        if not meter_id or not categories:
            return JsonResponse({'error': 'Meter ID and Controller IP is required'}, status=status.HTTP_400_BAD_REQUEST)
        d = Device.objects.get(lan_ip_address=controller_ip)
        if mac_address:
            network_device = NetworkDevice.objects.get(mac_address=mac_address)
            meter = Meter.objects.get(meter_id=meter_id, controller_device=d, network_device=network_device)
            existing_categories = Category.objects.filter(meter__controller_device=meter.controller_device, meter__network_device=network_device).exclude(
                meter=meter)
        else:
            meter = Meter.objects.get(meter_id=meter_id, controller_device=d)
            existing_categories = Category.objects.filter(meter__controller_device=meter.controller_device).exclude(
                meter=meter)

        meter.categories.clear()
        for cat_name in categories:
            category, _ = Category.objects.get_or_create(name=cat_name)
            if category in existing_categories:
                raise ValidationError(f"Category '{category.name}' is already in use on this device.")
            meter.categories.add(category)
        meter.save()

        return JsonResponse({'message': 'Meter updated successfully'}, status=status.HTTP_200_OK)
    except Meter.DoesNotExist:
        return JsonResponse({'error': 'Meter not found'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def delete_meter(request):
    controller_ip = request.data.get('controller_ip')
    device_id = request.data.get('deviceId', None)
    onos_meter_id = request.data.get('onosMeterId', None)
    db_meter_id = request.data.get('meterId', None)
    meter_db = Meter.objects.get(id=db_meter_id)
    onos_meter_id = convert_onos_meter_api_id_to_internal_id(onos_meter_id)

    if not device_id or not db_meter_id or not onos_meter_id:
        return JsonResponse({'error': 'Missing required fields: deviceId, meterId and onosMeterId required.'}, status=400)

    device_id_encoded = urllib.parse.quote(device_id, safe='')  # URL encode the device ID
    print(device_id)
    print(onos_meter_id)
    url = f"http://{controller_ip}:8181/onos/v1/meters/{device_id_encoded}/{onos_meter_id}"
    print(url)
    response = requests.delete(
        url=url,
        headers={'Accept': 'application/json'},
        auth=HTTPBasicAuth('onos', 'rocks')
    )
    print(response.text)
    if response.status_code == 204:  # Depending on the server, it may return 204 for a successful delete
        meter_db.delete()
        return JsonResponse({'message': 'Meter deleted successfully'}, status=200)
    else:
        print(response)
        return JsonResponse({'error': 'Failed to delete meter on ONOS server'}, status=500)


@api_view(['GET'])
def get_device_details(request):
    device_id = request.GET.get('deviceId', None)
    print(device_id)
    url = "http://127.0.0.1:8181/onos/v1/devices/"
    if device_id:
        device_id_encoded = urllib.parse.quote(device_id, safe='')  # URL encode the device ID
        url = f"http://127.0.0.1:8181/onos/v1/devices/{device_id_encoded}"

    response = requests.get(
        url=url,
        headers={'Accept': 'application/json'},
        auth=HTTPBasicAuth('onos', 'rocks')
    )
    return Response(response.json(), status=response.status_code)


@api_view(['GET'])
def get_port_details(request):
    device_id = request.GET.get('deviceId', None)
    print(device_id)
    if device_id:
        device_id_encoded = urllib.parse.quote(device_id, safe='')  # URL encode the device ID
        url = f"http://127.0.0.1:8181/onos/v1/devices/{device_id_encoded}/ports"
        response = requests.get(
            url=url,
            headers={'Accept': 'application/json'},
            auth=HTTPBasicAuth('onos', 'rocks')
        )
        return Response(response.json(), status=response.status_code)
    else:
        return JsonResponse({'error': 'Failed to get device port details on ONOS server'}, status=500)


@api_view(['POST'])
def delete_flows(request):
    app_id = request.data.get('appId', None)
    if not app_id:
        return JsonResponse({'error': 'Missing App ID in request data'}, status=400)

    app_id_encoded = urllib.parse.quote(app_id, safe='')  # encode
    print(app_id)
    url = f"http://127.0.0.1:8181/onos/v1/flows/application/{app_id}"
    print(url)
    response = requests.delete(
        url=url,
        headers={'Accept': 'application/json'},
        auth=HTTPBasicAuth('onos', 'rocks')
    )
    print(response.text)
    if response.status_code == 204:  # Depending on the server, it may return 204 for a successful delete
        return JsonResponse({'message': 'Flows deleted successfully'}, status=200)
    else:
        print(response)
        return JsonResponse({'error': 'Failed to delete flows on ONOS server'}, status=500)

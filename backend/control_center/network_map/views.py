from django.shortcuts import render
import requests
import os
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from requests.auth import HTTPBasicAuth
from general.models import Device, Bridge
from ovs_install.utilities.utils import write_to_inventory, save_ip_to_config, save_bridge_name_to_config, \
    save_interfaces_to_config, save_controller_port_to_config, save_controller_ip_to_config
from ovs_install.utilities.ovs_results_format import format_ovs_dump_flows
from ovs_install.utilities.ansible_tasks import run_playbook
import logging

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
logger = logging.getLogger(__name__)
playbook_dir_path = f"{parent_dir}/ansible/playbooks"
inventory_path = f"{parent_dir}/ansible/inventory/inventory"
config_path = f"{parent_dir}/ansible/group_vars/all.yml"
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)


class OnosNetworkMap(APIView):
    def get(self, request):
        try:
            username = 'onos'
            password = 'rocks'
            headers = {'Accept': 'application/json'}
            links_url = 'http://10.10.10.4:8181/onos/v1/links'
            clusters_url = 'http://10.10.10.4:8181/onos/v1/topology/clusters'
            devices_info_url = 'http://10.10.10.4:8181/onos/v1/devices'

            links_response = requests.get(links_url, headers=headers, auth=HTTPBasicAuth(username, password))
            clusters_response = requests.get(clusters_url, headers=headers, auth=HTTPBasicAuth(username, password))
            devices_info_responses = requests.get(devices_info_url, headers=headers,
                                                  auth=HTTPBasicAuth(username, password))

            if links_response.status_code == 200 and clusters_response.status_code == 200 and devices_info_responses.status_code == 200:
                links_data = links_response.json()['links']
                clusters_data = clusters_response.json()['clusters']
                devices_info_data = devices_info_responses.json()['devices']
                data = {
                    'links': links_data,
                    'clusters': clusters_data,
                    'device_info': devices_info_data
                }
                print(data)

                return JsonResponse(data)
            else:
                return Response({"status": "error", "message": 'Failed to fetch data from ONOS API'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(e)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OvsNetworkMap(APIView):
    def get(self, request):
        data_resp = {}
        try:
            bridges = Bridge.objects.all()
            for bridge in bridges:
                data_resp[bridge.device.name] = {'bridges': []}
                temp_data = {'name': bridge.name, 'flows': None}
                if bridge.controller:
                    temp_data['controller_name'] = bridge.controller.device.name
                    temp_data['controller_ip'] = bridge.controller.device.lan_ip_address
                    temp_data['controller_type'] = bridge.controller.type
                bridge_name = bridge.name
                device = bridge.device
                lan_ip_address = device.lan_ip_address
                save_bridge_name_to_config(bridge_name, config_path)
                write_to_inventory(lan_ip_address, device.username, device.password, inventory_path)
                save_ip_to_config(lan_ip_address, config_path)
                dump_flows = run_playbook('ovs-gather-network-data', playbook_dir_path, inventory_path)
                if dump_flows.get('status') == 'success':
                    results = dump_flows['results']
                    bridge_flows = format_ovs_dump_flows(results)
                    # data_resp[bridge_name] = bridge_flows
                    temp_data['flows'] = bridge_flows
                data_resp[bridge.device.name]['bridges'].append(temp_data)
            return Response({'status': 'success', 'data': data_resp},
                            status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

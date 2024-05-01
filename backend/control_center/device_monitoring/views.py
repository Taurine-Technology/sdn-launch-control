from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import os
from rest_framework.decorators import api_view
from ovs_install.utilities.ansible_tasks import run_playbook
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError
import logging
from ovs_install.utilities.utils import write_to_inventory, save_ip_to_config, save_bridge_name_to_config, \
    save_interfaces_to_config, save_openflow_version_to_config, save_controller_port_to_config, \
    save_controller_ip_to_config, save_api_url_to_config
from rest_framework.response import Response
from rest_framework import status

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
logger = logging.getLogger(__name__)
install_system_monitor = "install-stats-monitor"
install_qos_monitor = "run-ovs-qos-monitor"
playbook_dir_path = f"{parent_dir}/ansible/playbooks"
inventory_path = f"{parent_dir}/ansible/inventory/inventory"
config_path = f"{parent_dir}/ansible/group_vars/all.yml"


# TODO test this
@api_view(['POST'])
def install_system_stats_monitor(request):
    try:
        data = request.data
        validate_ipv4_address(data.get('lan_ip_address'))
        lan_ip_address = data.get('lan_ip_address')
        write_to_inventory(lan_ip_address, data.get('username'), data.get('password'), inventory_path)
        save_ip_to_config(lan_ip_address, config_path)
        save_api_url_to_config(data.get('api_url'), config_path)
        result_install = run_playbook(install_system_monitor, playbook_dir_path, inventory_path)
    except ValidationError:
        return Response({"status": "error", "message": "Invalid IP address format."},
                        status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(e)
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# TODO test this
@api_view(['POST'])
def install_ovs_qos_monitor(request):
    try:
        data = request.data
        validate_ipv4_address(data.get('lan_ip_address'))
        lan_ip_address = data.get('lan_ip_address')
        bridge_name = data.get('bridge_name')
        openflow_version = data.get('openflow_version')
        save_openflow_version_to_config(openflow_version, config_path)
        save_bridge_name_to_config(bridge_name, config_path)
        write_to_inventory(lan_ip_address, data.get('username'), data.get('password'), inventory_path)
        save_ip_to_config(lan_ip_address, config_path)
        save_api_url_to_config(data.get('api_url'), config_path)
        result_install = run_playbook(install_qos_monitor, playbook_dir_path, inventory_path)
    except ValidationError:
        return Response({"status": "error", "message": "Invalid IP address format."},
                        status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(e)
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
def post_device_stats(request):
    try:

        # Parse the JSON data from the request
        data = json.loads(request.body)
        # Get the channel layer and send the data to the 'device_stats' group
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'device_stats',
            {
                'type': 'device.message',
                'device': data
            }
        )
        return Response({"status": "success"}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
def post_openflow_metrics(request):
    try:
        data = json.loads(request.body)
        device_ip = data['device_ip']
        stats = data['stats']
        throughput_data = {
            'ip_address': device_ip,
            'ports': {}
        }

        for port, values in stats.items():
            # Calculate throughput in bytes per second
            if values['duration_diff'] > 0:
                throughput_bps = (values['rx_bytes_diff'] * 8) / values['duration_diff']
                throughput_mbps = throughput_bps / 1000000
            else:
                throughput_mbps = 0
            throughput_data['ports'][port] = throughput_mbps

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "openflow_metrics",
            {
                "type": "openflow_message",
                "message": throughput_data
            }
        )
        return Response({"status": "success"}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json


@csrf_exempt
@require_http_methods(["POST"])
def post_device_stats(request):
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
    return JsonResponse({'status': 'received'}, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def post_openflow_metrics(request):
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
    print(throughput_data)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "openflow_metrics",
        {
            "type": "openflow_message",
            "message": throughput_data
        }
    )
    return JsonResponse({"status": "success"}, status=200)

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

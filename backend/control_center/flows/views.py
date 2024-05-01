from rest_framework.decorators import api_view
from rest_framework import status
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import csrf_exempt
import json


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

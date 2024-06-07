from rest_framework.decorators import api_view
from rest_framework import status
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import csrf_exempt
import json
from classifier import classification_model
from classifier.classification import create_classification_from_json
import os
path = os.getcwd()
classifier_folder = os.path.join(path, 'classifier/ml_models/attention-random-model-23-8400')
print(classifier_folder)
classifier = classification_model.ClassificationModel(classifier_folder, 23)


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
        data = json.loads(request.body)
        model_name = data.get('model_name')
        classification = create_classification_from_json(data)
        result = classifier.predict_flow(classification.payload)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'flow_updates',
            {
                'type': 'flow_message',
                'flow': result[0]
            }
        )
        return JsonResponse({'message': 'received'}, status=status.HTTP_200_OK)

from rest_framework.decorators import api_view
from rest_framework import status
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import csrf_exempt
import json
from classifier import classification_model
from classifier.classification import create_classification_from_json
from classifier.meter_flow_rule import MeterFlowRule
from general.models import Controller, Plugins, Device
from onos.models import Category, Meter
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
        # check if classifier and meter plugin are installed
        classifier_plugin = Plugins.objects.get(name='tau-traffic-classification-sniffer')
        meter_plugin = Plugins.objects.get(name='tau-traffic-classification-sniffer')
        installed = meter_plugin.installed and classifier_plugin.installed


        data = json.loads(request.body)
        model_name = data.get('model_name')
        switch_ip = data.get('lan_ip_address')
        classification = create_classification_from_json(data)
        result = classifier.predict_flow(classification.payload)
        application = result[0]
        print(application)
        print(installed)
        meter = None
        if installed:
            switch_device = Device.objects.get(lan_ip_address=switch_ip, device_type='switch')
            controller = Controller.objects.get(switches=switch_device, type='onos')
            print('Checking for meter entry')
            if Meter.objects.filter(categories__name=application, controller_device=controller.device).exists():
                print('FOUND METER MATCHING ENTRY')
                meter = Meter.objects.get(categories__name=application, controller_device=controller.device)
                proto = 'udp'
                if data.get('tcp') == 1:
                    proto = 'tcp'
                flow_rule = MeterFlowRule(
                    proto=proto, client_port=classification.client_port, outbound_port=classification.outbound_port,
                    inbound_port=classification.inbound_port, category=application,
                    src_mac=classification.src_mac, controller_ip=meter.controller_device.lan_ip_address,
                    meter_id=meter.meter_id, switch_id=meter.switch_id
                )
                flow_rule.make_flow_adjustment()
            else:
                print('did not find entry')
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'flow_updates',
            {
                'type': 'flow_message',
                'flow': result[0]
            }
        )
        print(result)
        return JsonResponse({'message': 'received'}, status=status.HTTP_200_OK)

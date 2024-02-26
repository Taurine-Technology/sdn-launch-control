from django.shortcuts import render
import requests
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from requests.auth import HTTPBasicAuth
# Create your views here.
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
            devices_info_responses = requests.get(devices_info_url, headers=headers, auth=HTTPBasicAuth(username, password))

            if links_response.status_code == 200 and clusters_response.status_code == 200 and devices_info_responses.status_code == 200:
                links_data = links_response.json()['links']
                clusters_data = clusters_response.json()['clusters']
                devices_info_data = devices_info_responses.json()['devices']
                data = {
                    'links': links_data,
                    'clusters': clusters_data,
                    'device_info': devices_info_data
                }

                return JsonResponse(data)
            else:
                return Response({"status": "error", "message": 'Failed to fetch data from ONOS API'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(e)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
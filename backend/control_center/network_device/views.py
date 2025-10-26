# views.py
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import NetworkDevice
from .serializers import NetworkDeviceSerializer
from rest_framework.pagination import PageNumberPagination
from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

class NetworkDevicePagination(PageNumberPagination):
    page_size = 25  # Default page size, can be overridden by ?page_size= param
    page_size_query_param = 'page_size'
    max_page_size = 200

class NetworkDeviceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows network devices to be viewed, edited, searched, and filtered.
    """
    queryset = NetworkDevice.objects.all()
    serializer_class = NetworkDeviceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'mac_address', 'name', 'device_type', 'verified', 'ip_address']
    search_fields = ['name', 'mac_address', 'ip_address']
    ordering_fields = ['id', 'name', 'mac_address', 'device_type', 'ip_address', 'verified']
    ordering = ['id']
    pagination_class = NetworkDevicePagination
    
    @action(detail=False, methods=['get'])
    def monitored(self, request):
        """
        Returns only network devices that are actively being monitored.
        
        This endpoint filters devices where is_ping_target=True, meaning
        they are being pinged every 60 seconds by the monitoring system.
        
        Supports all standard filtering, searching, and pagination that
        applies to the main device list endpoint.
        
        Example:
            GET /api/network-devices/monitored/
            GET /api/network-devices/monitored/?search=router
            GET /api/network-devices/monitored/?device_type=switch
            
        Returns:
            List of monitored NetworkDevice objects
        """
        # Start with the base queryset (respects account filtering, etc.)
        queryset = self.filter_queryset(self.get_queryset())
        
        # Filter to only monitored devices
        monitored_devices = queryset.filter(is_ping_target=True)
        
        # Apply pagination
        page = self.paginate_queryset(monitored_devices)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        # If pagination is disabled, return all results
        serializer = self.get_serializer(monitored_devices, many=True)
        return Response(serializer.data)


def _find_device_by_identifier(mac_address, ip_address):
    """
    Helper function to find a device by MAC address or IP address.
    
    Args:
        mac_address: MAC address to search for (optional)
        ip_address: IP address to search for (optional)
        
    Returns:
        tuple: (device, error_response)
            - device: NetworkDevice object if found, None otherwise
            - error_response: Response object with error details if device not found
    """
    if mac_address:
        try:
            device = NetworkDevice.objects.get(mac_address__iexact=mac_address)
            return device, None
        except NetworkDevice.DoesNotExist:
            return None, Response(
                {"error": "Device not found."},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        if not ip_address:
            return None, Response(
                {"error": "Either mac_address or ip_address must be provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            device = NetworkDevice.objects.get(ip_address=ip_address)
            return device, None
        except NetworkDevice.DoesNotExist:
            return None, Response(
                {"error": "Device not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except NetworkDevice.MultipleObjectsReturned:
            return None, Response(
                {"error": "Multiple devices found with this IP address. Please use MAC address instead."},
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_host_by_identifier(request):
    """
    Updates a NetworkDevice based on identifying fields in the payload.

    Expected payload:
    {
      "mac_address": "<mac address>" (optional),
      "ip_address": "<ip address>" (required if mac_address not provided),
      ... other fields to update ...
    }

    The view searches for a device using:
      - If a mac_address is provided: device with that mac address (case-insensitive)
      - Otherwise, it uses ip_address.
    """
    payload = request.data
    mac_address = payload.get("mac_address")
    ip_address = payload.get("ip_address")

    # Find the device using helper function
    device, error_response = _find_device_by_identifier(mac_address, ip_address)
    if error_response:
        return error_response

    # Update the device
    serializer = NetworkDeviceSerializer(device, data=payload, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_host_by_identifier(request):
    """
    Deletes a NetworkDevice based on identifying fields in the payload.

    Expected payload:
    {
      "mac_address": "<mac address>" (optional),
      "ip_address": "<ip address>" (required if mac_address not provided)
    }

    The view searches for a device using:
      - If a mac_address is provided: device with that mac address (case-insensitive)
      - Otherwise, it uses ip_address.
    """
    payload = request.data
    mac_address = payload.get("mac_address")
    ip_address = payload.get("ip_address")

    # Find the device using helper function
    device, error_response = _find_device_by_identifier(mac_address, ip_address)
    if error_response:
        return error_response

    # Delete the device
    device.delete()
    return Response(
        {"message": "Device deleted successfully."},
        status=status.HTTP_200_OK
    )

# views.py
from rest_framework import viewsets, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
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
    
    Supports lookup by:
    - Primary key (id): GET/PUT/DELETE /network-devices/{id}/
    - MAC address: GET/PUT/DELETE /network-devices/{mac_address}/
    - IP address: GET/PUT/DELETE /network-devices/{ip_address}/
    """
    queryset = NetworkDevice.objects.all()
    serializer_class = NetworkDeviceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id', 'mac_address', 'name', 'device_type', 'verified', 'ip_address']
    search_fields = ['name', 'mac_address', 'ip_address']
    ordering_fields = ['id', 'name', 'mac_address', 'device_type', 'ip_address', 'verified']
    ordering = ['id']
    pagination_class = NetworkDevicePagination
    
    def get_object(self):
        """
        Override get_object to support lookup by MAC address or IP address
        in addition to the default primary key lookup.
        """
        lookup_value = self.kwargs.get(self.lookup_field)
        
        # Try primary key lookup first (for numeric IDs)
        if lookup_value.isdigit():
            return super().get_object()
        
        # Try MAC address lookup (case-insensitive) - only if lookup_value looks like a MAC
        if ':' in lookup_value or '-' in lookup_value:
            try:
                return NetworkDevice.objects.get(mac_address__iexact=lookup_value)
            except NetworkDevice.DoesNotExist:
                pass
        
        # Try IP address lookup
        try:
            device = NetworkDevice.objects.get(ip_address=lookup_value)
            return device
        except NetworkDevice.DoesNotExist:
            pass
        except NetworkDevice.MultipleObjectsReturned:
            # If multiple devices have the same IP, raise a more specific error
            raise ValueError("Multiple devices found with this IP address. Please use MAC address instead.")
        
        # If no device found, raise 404
        raise NetworkDevice.DoesNotExist(f"Device not found with identifier: {lookup_value}")
    
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

# views.py
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import NetworkDevice
from .serializers import NetworkDeviceSerializer
from rest_framework.pagination import PageNumberPagination

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

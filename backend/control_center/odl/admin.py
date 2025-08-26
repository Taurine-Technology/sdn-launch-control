# odl_manager/admin.py
from django.contrib import admin
from .models import OdlMeter, Category
from general.models import Device # To filter controller_device choices
from network_device.models import NetworkDevice # To filter network_device choices

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_configuration', 'category_cookie')
    list_filter = ('model_configuration',)
    search_fields = ('name', 'model_configuration__name', 'category_cookie')
    readonly_fields = ('category_cookie',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'model_configuration')
        }),
        ('Technical Details', {
            'fields': ('category_cookie',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('model_configuration')

@admin.register(OdlMeter)
class OdlMeterAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'meter_id_on_odl',
        'switch_node_id',
        'controller_device_name', # Custom method to display controller name
        'rate',
        'meter_type',
        'network_device_mac', # Custom method
        'model_configuration', # Add model configuration
        'activation_period',
        'start_time',
        'end_time',
        'updated_at',
    )
    list_filter = (
        'meter_type',
        'activation_period',
        'controller_device',
        'switch_node_id',
        'model_configuration', # Add model configuration filter
        'categories',
    )
    search_fields = (
        'meter_id_on_odl',
        'switch_node_id',
        'controller_device__name', # Search by controller device name
        'controller_device__lan_ip_address', # Search by controller IP
        'network_device__mac_address', # Search by associated MAC
        'model_configuration__name', # Search by model name
        'categories__name',
    )
    filter_horizontal = ('categories',) # Better UI for ManyToManyField

    fieldsets = (
        (None, {
            'fields': ('controller_device', 'switch_node_id', 'meter_id_on_odl')
        }),
        ('Meter Configuration', {
            'fields': ('meter_type', 'rate', 'odl_flags')
        }),
        ('Association & Scheduling', {
            'fields': ('categories', 'network_device', 'model_configuration', 'activation_period', 'start_time', 'end_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',) # Collapsible section
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def controller_device_name(self, obj):
        if obj.controller_device:
            return obj.controller_device.name
        return "-"
    controller_device_name.short_description = 'Controller' # Column header

    def network_device_mac(self, obj):
        if obj.network_device:
            return obj.network_device.mac_address
        return "-"
    network_device_mac.short_description = 'Network Device MAC'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Filter 'controller_device' to only show devices of type 'controller'
        if db_field.name == "controller_device":
            kwargs["queryset"] = Device.objects.filter(device_type='controller')
        # You can add similar filtering for 'network_device' if needed,
        # e.g., to only show 'end_user' type devices.
        # if db_field.name == "network_device":
        #     kwargs["queryset"] = NetworkDevice.objects.filter(device_type='end_user')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        # Prefetch related data for efficiency in list display
        return super().get_queryset(request).select_related('controller_device', 'network_device', 'model_configuration').prefetch_related('categories')


# File: plugins/admin.py
from django.contrib import admin
from .models import Plugin, PluginRequirement, PluginInstallation, SnifferInstallationConfig
from django.core.exceptions import ValidationError

# --- Inline Admin for Sniffer Config ---
class SnifferInstallationConfigInline(admin.StackedInline):
    model = SnifferInstallationConfig
    can_delete = False # Deletion should happen via the parent or dedicated view
    verbose_name_plural = 'Sniffer Configuration'
    # Define fields to display/edit in the inline form
    fields = ('api_base_url', 'monitor_interface', 'port_to_client', 'port_to_router', 'bridge_name')
    # Make fields read-only if you don't want direct admin edits,
    # forcing users to use the API which includes re-installation logic.
    # readonly_fields = ('api_base_url', 'monitor_interface', 'port_to_client', 'port_to_router', 'bridge_name')

    # Add validation to prevent adding config to non-sniffer installs via admin
    def clean(self):
        super().clean()
        # Access the parent instance (PluginInstallation)
        if hasattr(self, 'instance') and self.instance and self.instance.pk: # Check if instance exists

            if self.instance.plugin.name != 'tau-traffic-classification-sniffer':
                raise ValidationError("Sniffer configuration can only be added to 'tau-traffic-classification-sniffer' installations.")

    # Control when this inline is displayed
    def has_add_permission(self, request, obj=None):
        # Prevent adding config directly if parent doesn't exist or isn't sniffer
        if obj and obj.plugin.name == 'tau-traffic-classification-sniffer':
             return True # Allow adding only if parent is sniffer
        return False # Disable adding otherwise

    def has_change_permission(self, request, obj=None):
         # Allow changing only if parent is sniffer
         if obj and obj.installation.plugin.name == 'tau-traffic-classification-sniffer':
             return True
         return False

    def has_delete_permission(self, request, obj=None):
        # Prevent direct deletion of config from here
        return False


@admin.register(Plugin)
class PluginAdmin(admin.ModelAdmin):
    list_display = ('name', 'alias', 'version', 'requires_target_device')
    search_fields = ('name', 'alias', 'author')


@admin.register(PluginRequirement)
class PluginRequirementAdmin(admin.ModelAdmin):
    list_display = ('plugin', 'required_plugin')
    list_filter = ('plugin',)


@admin.register(PluginInstallation)
class PluginInstallationAdmin(admin.ModelAdmin):
    list_display = ('id', 'plugin', 'device', 'installed_at', 'has_sniffer_config')
    list_filter = ('plugin', 'device', 'installed_at')
    search_fields = ('plugin__name', 'plugin__alias', 'device__name', 'device__lan_ip_address')
    readonly_fields = ('installed_at',)
    # Define which inlines to use
    inlines = []

    # Dynamically add the inline only for sniffer plugin installations
    def get_inlines(self, request, obj=None):
        # Check if we are viewing/editing a specific PluginInstallation object (obj)
        # and if that object's plugin is the sniffer plugin
        # Adjust check based on alias vs name
        if obj and obj.plugin.name == 'tau-traffic-classification-sniffer':
            return [SnifferInstallationConfigInline] # Add the inline
        return [] # Return empty list otherwise

    # Add a method to display in list_display if config exists
    @admin.display(boolean=True, description='Has Sniffer Config?')
    def has_sniffer_config(self, obj):
        # Check if the related sniffer_config exists for this installation
        return hasattr(obj, 'sniffer_config') and obj.sniffer_config is not None


@admin.register(SnifferInstallationConfig)
class SnifferInstallationConfigAdmin(admin.ModelAdmin):
    list_display = ('get_installation_id', 'get_device_ip', 'api_base_url', 'bridge_name')
    list_select_related = ('installation', 'installation__device', 'installation__plugin')
    search_fields = ('installation__device__lan_ip_address', 'installation__device__name', 'api_base_url', 'bridge_name')
    # Make all fields read-only if edits should only happen via the API/Inline
    readonly_fields = ('installation', 'api_base_url', 'monitor_interface', 'port_to_client', 'port_to_router', 'bridge_name')

    @admin.display(description='Installation ID')
    def get_installation_id(self, obj):
        return obj.installation.id

    @admin.display(description='Device IP')
    def get_device_ip(self, obj):
        return obj.installation.device.lan_ip_address if obj.installation.device else "N/A"

    # Prevent adding/deleting directly from this separate view
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def has_change_permission(self, request, obj=None):
        # Allow viewing but not changing directly here if readonly_fields is set
        return super().has_change_permission(request, obj) if not self.readonly_fields else False


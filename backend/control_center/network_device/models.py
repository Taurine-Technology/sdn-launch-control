# models.py
from django.core.validators import RegexValidator
from django.db import models
from account.models import Account
DEVICE_TYPES = (
    ('switch', 'Switch'),
    ('access_point', 'Access Point'),
    ('server', 'Server'),
    ('controller', 'Controller'),
    ('vm', 'Virtual Machine'),
    ('client', 'Client'),
    ('dns', 'DNS Server'),
    ('end_user', 'End User'),
)

OS_TYPES = (
    ('ubuntu_20_server', 'Ubuntu 20 Server'),
    ('ubuntu_22_server', 'Ubuntu 22 Server'),
    ('ubuntu_24_server', 'Ubuntu 24 Server'),
    ('ubuntu_20_desktop', 'Ubuntu 20 Desktop'),
    ('ubuntu_22_desktop', 'Ubuntu 22 Desktop'),
    ('ubuntu_24_desktop', 'Ubuntu 24 Desktop'),
    ('unknown', 'Unknown'),
    ('windows', 'Windows'),
    ('macos', 'macOS'),
    ('linux', 'Linux'),
    ('android', 'Android'),
    ('ios', 'iOS'),
    ('chromeos', 'ChromeOS'),
    ('chromebook', 'Chromebook'),
    ('other', 'Other'),
)

mac_address_validator = RegexValidator(
    regex=r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
    message="Enter a valid MAC address in format XX:XX:XX:XX:XX:XX."
)

class NetworkDevice(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="network_devices"
    )

    mac_address = models.CharField(max_length=17, unique=True, blank=True, null=True, validators=[mac_address_validator])
    name = models.CharField(max_length=100, blank=True, null=True)
    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_TYPES,
        default='unknown',
        blank=True,
        null=True,
    )
    operating_system = models.CharField(
        max_length=20,
        choices=OS_TYPES,
        default='unknown',
        blank=True,
        null=True,
    )
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    number_of_ports = models.IntegerField(blank=True, null=True)
    is_ping_target = models.BooleanField(default=False, db_index=True)
    openvswitch_enabled = models.BooleanField(default=False)
    openvswitch_version = models.CharField(max_length=50, blank=True, null=True)
    openflow_version = models.CharField(max_length=50, blank=True, null=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        if self.mac_address:
            return f"{self.name or 'Unnamed'} ({self.mac_address})"
        elif self.ip_address:
            return f"{self.name or 'Unnamed'} ({self.ip_address})"
        else:
            return f"{self.name or 'Unnamed'} (ID: {self.id})"

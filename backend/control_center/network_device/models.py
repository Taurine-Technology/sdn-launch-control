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
    ('end_user', 'End User'),
)

OS_TYPES = (
    ('ubuntu_20_server', 'Ubuntu 20 Server'),
    ('ubuntu_22_server', 'Ubuntu 22 Server'),
    ('unknown', 'Unknown'),
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

    mac_address = models.CharField(max_length=17, unique=True, validators=[mac_address_validator])
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
    openvswitch_enabled = models.BooleanField(default=False)
    openvswitch_version = models.CharField(max_length=50, blank=True, null=True)
    openflow_version = models.CharField(max_length=50, blank=True, null=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return self.mac_address

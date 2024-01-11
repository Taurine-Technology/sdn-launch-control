from django.db import models

# Create your models here.
class Device(models.Model):
    DEVICE_TYPES = (
        ('switch', 'Switch'),
        ('access_point', 'Access Point'),
        ('server', 'Server')
    )
    OS_TYPES = (
        ('ubuntu_20_server', 'Ubuntu 20 Server'),
        ('ubuntu_22_server', 'Ubuntu 22 Server'),
    )

    name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    os_type = models.CharField(max_length=20, choices=OS_TYPES)

    lan_ip_address = models.GenericIPAddressField(unique=True)

    # ovs specific fields
    ports = models.IntegerField(null=True)
    ovs_enabled = models.BooleanField(default=False)
    ovs_version = models.CharField(max_length=10, null=True)
    openflow_version = models.CharField(max_length=10, null=True)

    def __str__(self):
        return f"({self.name} {self.device_type})"
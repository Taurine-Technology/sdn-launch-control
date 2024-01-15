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
    num_ports = models.IntegerField(default=0)
    ovs_enabled = models.BooleanField(default=False)
    ovs_version = models.CharField(max_length=10, null=True)
    openflow_version = models.CharField(max_length=10, null=True)

    def __str__(self):
        return f"({self.name} {self.device_type})"


class Bridge(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='bridges')
    name = models.CharField(max_length=100)
    dpid = models.CharField(max_length=30)

    def __str__(self):
        return f"Bridge {self.name} on device {self.device.name}"


class Port(models.Model):
    bridge = models.ForeignKey(Bridge, on_delete=models.CASCADE, related_name='ports', null=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='ports')
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"Port {self.name} on {self.device.name}"

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
        ('other', 'Other'),
    )

    name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    os_type = models.CharField(max_length=20, choices=OS_TYPES)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

    lan_ip_address = models.GenericIPAddressField(unique=True)

    # ovs specific fields
    num_ports = models.IntegerField(default=0)
    ovs_enabled = models.BooleanField(default=False)
    ovs_version = models.CharField(max_length=10, blank=True, null=True)
    openflow_version = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"({self.name} {self.device_type})"


class Bridge(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='bridges')
    name = models.CharField(max_length=100)
    dpid = models.CharField(max_length=30)
    controller = models.ForeignKey('Controller', on_delete=models.SET_NULL, null=True, blank=True, related_name='bridges')
    def __str__(self):
        return f"Bridge {self.name} on device {self.device.name}"


class Port(models.Model):
    bridge = models.ForeignKey(Bridge, on_delete=models.SET_NULL, related_name='ports', null=True, blank=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='ports')
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"Port {self.name} on {self.device.name}"


class Controller(models.Model):
    TYPES = (
        ('onos', 'Onos'),
        ('odl', 'Open Daylight'),
        ('other', 'Other')
    )
    type = models.CharField(max_length=20, choices=TYPES)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='sdn_controller')
    lan_ip_address = models.GenericIPAddressField(unique=True)
    switches = models.ManyToManyField(Device, related_name='switch_controllers')


from django.db import models


# Create your models here.
class Device(models.Model):
    DEVICE_TYPES = (
        ('switch', 'Switch'),
        ('access_point', 'Access Point'),
        ('server', 'Server'),
        ('controller', 'Controller'),
        ('vm', 'Virtual Machine')
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
    controller = models.ForeignKey('Controller', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='bridges')

    def __str__(self):
        return f"Bridge {self.name} on device {self.device.name}"


class Port(models.Model):
    bridge = models.ForeignKey(Bridge, on_delete=models.SET_NULL, related_name='ports', null=True, blank=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='ports')
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('device', 'name')

    def __str__(self):
        return f"Port {self.name} on {self.device.name}"


# TODO make this work for multiple controllers on the same host
class Controller(models.Model):
    TYPES = (
        ('onos', 'Onos'),
        ('odl', 'Open Daylight'),
        ('faucet', 'Faucet'),
        ('other', 'Other')
    )
    type = models.CharField(max_length=20, choices=TYPES)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='sdn_controller')
    switches = models.ManyToManyField(Device, related_name='switch_controllers')
    port_num = models.IntegerField(default=6653)


class ClassifierModel(models.Model):
    name = models.CharField(max_length=20)
    number_of_bytes = models.IntegerField()
    number_of_packets = models.IntegerField()
    categories = models.CharField(max_length=1000)

    def __str__(self):
        return self.name


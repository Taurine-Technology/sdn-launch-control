# File: general/models.py
# Copyright (C) 2025 Taurine Technology
#
# This file is part of the SDN Launch Control project.
#
# This project is licensed under the GNU General Public License v3.0 (GPL-3.0),
# available at: https://www.gnu.org/licenses/gpl-3.0.en.html#license-text
#
# Contributions to this project are governed by a Contributor License Agreement (CLA).
# By submitting a contribution, contributors grant Taurine Technology exclusive rights to
# the contribution, including the right to relicense it under a different license
# at the copyright owner's discretion.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the GNU General Public License for more details.
#
# For inquiries, contact Keegan White at keeganwhite@taurinetech.com.

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
        ('unknown', 'Unknown'),
        ('other', 'Other'),
    )

    name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    os_type = models.CharField(max_length=20, choices=OS_TYPES)
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=100,  blank=True, null=True)

    lan_ip_address = models.GenericIPAddressField()

    # ovs specific fields
    num_ports = models.IntegerField(default=0)
    ovs_enabled = models.BooleanField(default=False)
    ovs_version = models.CharField(max_length=10, blank=True, null=True)
    openflow_version = models.CharField(max_length=10, blank=True, null=True)
    api_url = models.URLField(max_length=200, null=True, blank=True)

    class Meta:
        # This ensures that the combination of device_type and lan_ip_address is unique
        unique_together = (('device_type', 'lan_ip_address'),)

    def __str__(self):
        return f"({self.name} {self.device_type})"


class Bridge(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='bridges')
    name = models.CharField(max_length=100)
    dpid = models.CharField(max_length=30)
    controller = models.ForeignKey('Controller', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='bridges')
    api_url = models.URLField(max_length=200, null=True, blank=True)
    odl_node_id = models.CharField(max_length=255, blank=True, null=True,)

    class Meta:
        unique_together = ('device', 'name')  # Enforce unique bridge names per device

    def __str__(self):
        return f"Bridge {self.name} on device {self.device.name}"


class Port(models.Model):
    bridge = models.ForeignKey(Bridge, on_delete=models.SET_NULL, related_name='ports', null=True, blank=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='ports')
    name = models.CharField(max_length=100)
    ovs_port_number = models.IntegerField(null=True, blank=True)
    link_speed = models.IntegerField(null=True, blank=True, help_text="Link speed in Mb/s")
    is_up = models.BooleanField(null=True, blank=True, help_text="Port status: True if up, False if down, None if unknown")

    class Meta:
        unique_together = ('device', 'name')

    def __str__(self):
        if self.bridge:
            ovs_num_str = f" (OVS Port: {self.ovs_port_number})" if self.ovs_port_number is not None else ""
            return f"Port {self.name} on {self.device.name} (Bridge: {self.bridge.name}{ovs_num_str})"
        else:
            return f"Port {self.name} on {self.device.name} (Unassigned)"


# TODO make this work for multiple controllers on the same host
class Controller(models.Model):
    TYPES = (
        ('onos', 'Onos'),
        ('odl', 'Open Daylight'),
        ('faucet', 'Faucet'),
        ('unknown', 'Unknown'),
        ('other', 'Other')
    )
    type = models.CharField(max_length=20, choices=TYPES)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='sdn_controller')
    switches = models.ManyToManyField(Device, related_name='switch_controllers', blank=True)
    port_num = models.IntegerField(default=6653)


class ClassifierModel(models.Model):
    name = models.CharField(max_length=100)
    number_of_bytes = models.IntegerField()
    number_of_packets = models.IntegerField()
    categories = models.CharField(max_length=1000)

    def __str__(self):
        return self.name


class Plugins(models.Model):
    alias = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=100)
    short_description = models.CharField(max_length=200)
    long_description = models.CharField(max_length=500)
    author = models.CharField(max_length=100)
    installed = models.BooleanField(default=False)
    target_devices = models.ManyToManyField(Device, related_name='installed_devices', blank=True)


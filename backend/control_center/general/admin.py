# File: admin.py
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

from django.contrib import admin

# Register your models here.
from .models import Device, Bridge, Port, Controller, ClassifierModel, Plugins


@admin.register(Device)
class NetworkDeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'lan_ip_address', 'device_type', 'os_type', 'ovs_enabled')


@admin.register(Bridge)
class DeviceBridgeAdmin(admin.ModelAdmin):
    list_display = ('device', 'name', 'dpid')


@admin.register(Port)
class BridgePorts(admin.ModelAdmin):
    list_display = ('name', 'device')


@admin.register(Controller)
class ControllerAdmin(admin.ModelAdmin):
    list_display = ('type', 'device')


@admin.register(ClassifierModel)
class ClassifierModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'number_of_bytes', 'number_of_packets')

@admin.register(Plugins)
class PluginsAdmin(admin.ModelAdmin):
    list_display = ('alias', 'installed')
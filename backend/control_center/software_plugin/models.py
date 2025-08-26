# File: models.py
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
from general.models import Device

class Plugin(models.Model):
    alias = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=20)
    short_description = models.CharField(max_length=200)
    long_description = models.TextField()
    author = models.CharField(max_length=100)
    requires_target_device = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} (v{self.version})"

class PluginRequirement(models.Model):
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE, related_name="requirements")
    required_plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE, related_name="dependent_plugins")

    class Meta:
        unique_together = ('plugin', 'required_plugin')

    def __str__(self):
        return f"{self.plugin.name} requires {self.required_plugin.name}"

class PluginInstallation(models.Model):
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE, related_name="installations")
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="installed_plugins", null=True, blank=True)
    installed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('plugin', 'device')

    def __str__(self):
        return f"{self.plugin.name} installed on {self.device.lan_ip_address if self.device else 'Server'}"

class SnifferInstallationConfig(models.Model):
    # Link directly to the specific installation record
    installation = models.OneToOneField(
        PluginInstallation,
        on_delete=models.CASCADE,
        related_name="sniffer_config",
        primary_key=True,
    )
    # Add the configuration fields here
    api_base_url = models.URLField(max_length=255)
    monitor_interface = models.CharField(max_length=100)
    port_to_client = models.CharField(max_length=100)
    port_to_router = models.CharField(max_length=100)
    bridge_name = models.CharField(max_length=100)


    def __str__(self):
        return f"Sniffer Config for Installation ID {self.installation.id} on {self.installation.device.lan_ip_address if self.installation.device else 'Server'}"

    def clean(self):
        from django.core.exceptions import ValidationError
        # Ensure the related installation is for the correct plugin
        if self.installation.plugin.name != 'tau-traffic-classification-sniffer':
             raise ValidationError("This configuration can only be linked to a 'tau-traffic-classification-sniffer' plugin installation.")

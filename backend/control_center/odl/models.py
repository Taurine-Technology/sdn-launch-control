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
from django.utils.translation import gettext_lazy as _
from general.models import Device  # For linking to the ODL controller device
from network_device.models import NetworkDevice # For user-specific meters
import hashlib

def generate_category_cookie(category_name, model_name=None):
    """Helper function to generate a deterministic cookie from a category name and model."""
    if not category_name:
        return None
    # Include model name in the seed to ensure uniqueness across models
    if model_name:
        cookie_seed_str = f"{category_name}:{model_name}"
    else:
        cookie_seed_str = f"{category_name}"  # Fallback for legacy categories
    cookie_hasher = hashlib.sha1(cookie_seed_str.encode('utf-8'))
    cookie_hex_digest = cookie_hasher.hexdigest()
    # Using first 16 hex chars for a 64-bit integer representation
    # Store as BigIntegerField as cookies are 64-bit
    return int(cookie_hex_digest[:16], 16)

class Category(models.Model):
    name = models.CharField(max_length=255)  # Remove unique=True
    category_cookie = models.CharField(max_length=255, unique=True, null=True, blank=True, editable=False,
                                             help_text="Deterministic 64-bit cookie generated from the category name.")
    # Optional link to model configuration for model-specific categories
    model_configuration = models.ForeignKey(
        'classifier.ModelConfiguration',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='odl_categories',
        help_text="Model configuration this category belongs to (optional for backwards compatibility)"
    )

    class Meta:
        # Ensure category names are unique within each model configuration
        unique_together = ['name', 'model_configuration']
        # Also ensure category_cookie remains unique across all categories
        constraints = [
            models.UniqueConstraint(
                fields=['category_cookie'],
                name='unique_category_cookie',
                condition=models.Q(category_cookie__isnull=False)
            )
        ]

    def save(self, *args, **kwargs):
        # Automatically generate the cookie if it's not set (e.g., on creation)
        if not self.category_cookie and self.name:
            model_name = self.model_configuration.name if self.model_configuration else None
            self.category_cookie = generate_category_cookie(self.name, model_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (Cookie: {self.category_cookie or 'N/A'})"

class OdlMeter(models.Model):
    METER_TYPES = (('drop', 'drop'),)

    controller_device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='odl_meters',
        limit_choices_to={'device_type': 'controller'},
        help_text="The OpenDaylight controller device managing this meter."
    )
    # ODL's numeric meter ID. Serializer will map this to 'meter_id'.
    meter_id_on_odl = models.CharField(
        max_length=50,
        help_text="The numeric ID of the meter on OpenDaylight (e.g., '1', '22')."
    )
    meter_type = models.CharField(max_length=30, choices=METER_TYPES, default='drop')
    rate = models.IntegerField(help_text="Rate in Kbps for 'drop' type")
    # ODL node-id. Serializer will map this to 'switch_id'.
    switch_node_id = models.CharField(
        max_length=255,
        help_text="OpenDaylight Node ID of the switch (e.g., 'openflow:123...')."
    )
    # ODL flags, e.g., "meter-kbps", "meter-pps meter-burst"
    # We'll use this to derive 'unit' in the serializer.
    odl_flags = models.CharField(max_length=100, blank=True, help_text="Flags from ODL meter config (e.g., meter-kbps).")

    categories = models.ManyToManyField(Category, blank=True, related_name='odl_meters')
    network_device = models.ForeignKey(
        NetworkDevice,
        on_delete=models.CASCADE,
        related_name='odl_network_device_meters',
        null=True,
        blank=True,
    )
    
    # Optional link to model configuration for model-specific meters
    model_configuration = models.ForeignKey(
        'classifier.ModelConfiguration',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='odl_meters',
        help_text="Model configuration this meter is associated with (optional for backwards compatibility)"
    )

    WEEKDAY = 'weekday'
    WEEKEND = 'weekend'
    ALL_WEEK = 'all_week'
    TIME_PERIOD_CHOICES = [
        (WEEKDAY, _('Weekday')),
        (WEEKEND, _('Weekend')),
        (ALL_WEEK, _('All Week')),
    ]
    activation_period = models.CharField(
        max_length=10, choices=TIME_PERIOD_CHOICES, default=ALL_WEEK
    )
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            'controller_device',
            'switch_node_id',
            'meter_id_on_odl',
        )
        verbose_name = "OpenDaylight Meter"
        verbose_name_plural = "OpenDaylight Meters"
        indexes = [
            models.Index(fields=['controller_device', 'switch_node_id']),
        ]

    def __str__(self):
        return f"ODL Meter {self.meter_id_on_odl} on {self.switch_node_id} via {self.controller_device.name}"
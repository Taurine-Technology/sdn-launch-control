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

from django.core.exceptions import ValidationError
from django.db import models
from general.models import Device


# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Meter(models.Model):
    METER_TYPES = (('drop', 'drop'),)
    controller_device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='meters')
    meter_id = models.CharField(unique=True,max_length=30)
    meter_type = models.CharField(max_length=30, choices=METER_TYPES)
    rate = models.IntegerField()
    switch_id = models.CharField(max_length=30)
    categories = models.ManyToManyField(Category, blank=True)


class OnosOpenFlowDevice(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='openflow_device')
    openflow_id = models.CharField(max_length=30)

# File: urls.py
# Copyright (C) 2025 Taurine Technology
#
# This file is part of the SDN Launch Control project.
#
# This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0),
# available at: https://www.gnu.org/licenses/agpl-3.0.en.html#license-text
#
# Contributions to this project are governed by a Contributor License Agreement (CLA).
# By submitting a contribution, contributors grant Taurine Technology exclusive rights to
# the contribution, including the right to relicense it under a different license
# at the copyright owner's discretion.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the GNU Affero General Public License for more details.
#
# For inquiries, contact Keegan White at keeganwhite@taurinetech.com.

"""
URL configuration for SNMP monitoring API endpoints.

Registered endpoints:
- /snmp-devices/ - CRUD operations for SNMP device configuration
- /snmp-metrics/ - Read-only access to device metrics
- /snmp-interface-stats/ - Read-only access to interface statistics
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SNMPDeviceViewSet,
    SNMPMetricsViewSet,
    SNMPInterfaceStatsViewSet,
)

app_name = 'snmp_monitoring'

router = DefaultRouter()
router.register(r'snmp-devices', SNMPDeviceViewSet, basename='snmp-devices')
router.register(r'snmp-metrics', SNMPMetricsViewSet, basename='snmp-metrics')
router.register(r'snmp-interface-stats', SNMPInterfaceStatsViewSet, basename='snmp-interface-stats')

urlpatterns = [
    path('', include(router.urls)),
]


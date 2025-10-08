# File: urls.py
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
from django.urls import path, include
from ovs_management.views import GetBridgePortsView
from ovs_install.views import InstallOvsView
from ovs_management.views import EditBridge, GetDevicePorts, CreateBridge, GetDeviceBridges, DeleteBridge, DeleteControllerView, GetUnassignedDevicePorts
from controller.views import InstallControllerView
from classifier.views import classify, ClassificationStatsView
from onos.views import MeterListView, CreateMeterView, SwitchList, MeterListByIdView, update_meter, delete_meter
from device_monitoring.views import post_device_stats, post_openflow_metrics, install_system_stats_monitor, install_ovs_qos_monitor, install_sniffer
from general.views import (AddDeviceView, DeviceDetailView, DeviceListView, PluginListView, InstallPluginDatabaseAlterView, UninstallPluginDatabaseAlterView, CheckPluginInstallation, InstallPluginView,
                           CheckDeviceConnectionView, DeleteDeviceView, ForceDeleteDeviceView, UpdateDeviceView,
                            CategoryListView)
from network_map.views import OnosNetworkMap, OvsNetworkMap
from odl.views import CreateOpenDaylightMeterView, odl_classify_and_apply_policy, OdlMeterDetailView, OdlMeterListView, OdlControllerNodesView, ModelManagementView, ModelLoadView, ModelInfoView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from knox import views as knox_views
from .views import LoginView
urlpatterns = [
    path('admin/', admin.site.urls),

    # OpenAPI schema (raw JSON format)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI (for local development)
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # ---- CONTROLLERS ----
    # GET /api/v1/controllers/: Lists all controllers.
    # POST /api/v1/controllers/: Creates a new controller.
    # GET /api/v1/controllers/<id>/: Retrieves details of a specific controller by its id.
    # PUT /api/v1/controllers/<id>/: Updates an existing controller.
    # DELETE /api/v1/controllers/<id>/: Deletes a controller.
    # GET /api/v1/controllers/onos/: gets onos controllers
    # GET /api/v1/controllers/<id>/switches/: get list of switches for a controller
    # ---- SWITCHES ----
    # GET /api/v1/switches/: List all switches.
    # POST /api/v1/switches/: Create a new switch.
    # GET /api/v1/switches/<id>/: Retrieve details of a specific switch.
    # PUT /api/v1/switches/<id>/: Update a switch.
    # DELETE /api/v1/switches/<id>/: Delete a switch.
    # GET /api/v1/switches/<id>/ports/: List ports associated with a specific switch.
    # GET /api/v1/switches/<id>/bridges/: List bridges associated with a specific switch.
    path('api/v1/', include(
        'general.urls', namespace='general'
    )),

    path('api/v1/', include('network_device.urls', namespace='network_device')),

    path('api/v1/', include(
        'software_plugin.urls', namespace='plugins'
    )),
    path('api/v1/', include('network_data.urls', namespace='network_data')),

    # ---- Notification ----
    path('api/v1/', include('notification.urls', namespace='notification')),

# ---- account ----
    path('api/v1/', include('account.urls', namespace='account')),


    # ---- Knox ----
    path(r'api/v1/auth/login/', LoginView.as_view(), name='knox_login'),
     path(r'api/v1/auth/logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
     path(r'api/v1/auth/logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),

    # ---- INSTALL ----
    path('api/v1/install-ovs/', InstallOvsView.as_view(), name='install-ovs'),
    path('api/v1/install-controller/<str:controller_type>/', InstallControllerView.as_view(), name='install-controller'),

    # ---- CLASSIFIER ----
    path('api/v1/classify/', classify, name='classify'),
    path('api/v1/classification-stats/', ClassificationStatsView.as_view(), name='classification-stats'),

    # ---- DEVICES ----
    path('api/v1/devices/', DeviceListView.as_view(), name='device-list'),
    path('api/v1/add-device/', AddDeviceView.as_view(), name='add-device'),
    path('api/v1/device-details/<str:device_id>/', DeviceDetailView.as_view(), name='device-details'),


    path('api/v1/unassigned-device-ports/<str:lan_ip_address>/', GetUnassignedDevicePorts.as_view(), name='unassigned-device-ports'),
    path('api/v1/get-device-ports/<str:lan_ip_address>/', GetDevicePorts.as_view(), name='get-device-ports'),

    # ---- ONOS ----
    path('api/v1/onos/meters/<str:lan_ip_address>/', MeterListView.as_view(), name='onos-meter-list'),
    path('api/v1/onos/meters/<str:lan_ip_address>/<str:id>/', MeterListByIdView.as_view(), name='onos-meter-list-by-id'),
    path('api/v1/onos/create-meter/', CreateMeterView.as_view(), name='onos-create-metere'),
    path('api/v1/onos/devices/<str:controller_ip>/', SwitchList.as_view(), name='onos-list-devices'),
    path('api/v1/update_meter/', update_meter, name='onos-update-meter'),
    path('api/v1/delete_meter/', delete_meter, name='onos-delete-meter'),

    # ---- ODL ----
    path('api/v1/odl/create-meter/', CreateOpenDaylightMeterView.as_view(), name='odl-create-meter'),
    path('api/v1/odl/classify/', odl_classify_and_apply_policy, name='odl-classify'),
    path('api/v1/odl/meters/<int:pk>/', OdlMeterDetailView.as_view(), name='odl-meter-detail'),
    path('api/v1/odl/meters/', OdlMeterListView.as_view(), name='odl-meter-list'),

    path('api/v1/odl/controllers/<int:controller_id>/nodes/', OdlControllerNodesView.as_view(), name='odl-controller-nodes'),
    
    # ---- MODEL MANAGEMENT ----
    path('api/v1/models/', ModelManagementView.as_view(), name='model-management'),
    path('api/v1/models/load/', ModelLoadView.as_view(), name='model-load'),
    path('api/v1/models/info/', ModelInfoView.as_view(), name='model-info'),
    # ---- PLUGINS ----
    # path('api/v1/plugins/', PluginListView.as_view(), name='plugin-list'),
    # path('api/v1/plugins/check/<str:plugin_name>/', CheckPluginInstallation.as_view(), name='plugin-check'),
    # path('api/v1/plugins/install/<str:plugin_name>/', InstallPluginDatabaseAlterView.as_view(), name='plugin-install'),
    # path('api/v1/plugins/uninstall/<str:plugin_name>/', UninstallPluginDatabaseAlterView.as_view(), name='plugin-uninstall'),
    ####
    # path('api/v1/install-plugin/', InstallPluginView.as_view(), name='plugin-install'),
    path('api/v1/add-bridge/', CreateBridge.as_view(), name='add-bridge'),
    path('api/v1/devices/<str:lan_ip_address>/bridges/<str:bridge_name>/ports/', GetBridgePortsView.as_view(), name='get-bridge-ports'),
    path('api/v1/get-bridges/<str:lan_ip_address>/', GetDeviceBridges.as_view(), name='get-bridges'),
    path('api/v1/check-connection/<str:lan_ip_address>/<str:device_type>/', CheckDeviceConnectionView.as_view(), name='check-connection'),
    path('api/v1/delete-device/', DeleteDeviceView.as_view(), name='delete-device'),
    path('api/v1/force-delete-device/', ForceDeleteDeviceView.as_view(), name='force-delete-device'),
    path('api/v1/update-device/<str:lan_ip_address>/', UpdateDeviceView.as_view(), name='update_device'),
    path('api/v1/update-bridge/', EditBridge.as_view(), name='edit-bridge'),
    path('api/v1/delete-bridge/', DeleteBridge.as_view(), name='delete-bridge'),
    path('api/v1/onos-network-map/', OnosNetworkMap.as_view(), name='onos-network-map'),
    path('api/v1/ovs-network-map/', OvsNetworkMap.as_view(), name='ovs-network-map'),
    path('api/v1/post_device_stats/', post_device_stats, name='post_device_stats'),
    path('api/v1/post_openflow_metrics/', post_openflow_metrics, name='post_openflow_metrics'),

    path('api/v1/install_system_stats_monitor/', install_system_stats_monitor, name='install_system_stats_monitor'),
    path('api/v1/install-ovs-qos-monitor/', install_ovs_qos_monitor, name='install_ovs_qos_monitor'),
    path('api/v1/install-sniffer/', install_sniffer, name='install_sniffer'),

    path('api/v1/categories/', CategoryListView.as_view(), name='get-categories'),

]


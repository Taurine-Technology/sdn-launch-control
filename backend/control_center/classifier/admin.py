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
from .models import ModelConfiguration, ModelState


@admin.register(ModelConfiguration)
class ModelConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'display_name', 'model_type', 'num_categories', 
        'is_active', 'is_loaded', 'version', 'created_at'
    ]
    list_filter = ['model_type', 'is_active', 'is_loaded', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'description', 'version')
        }),
        ('Model Configuration', {
            'fields': ('model_type', 'model_path', 'input_shape', 'num_categories', 'confidence_threshold')
        }),
        ('Categories', {
            'fields': ('categories',),
            'description': 'List of category names for this model'
        }),
        ('Status', {
            'fields': ('is_active', 'is_loaded')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
    
    def save_model(self, request, obj, form, change):
        # Ensure only one model is active at a time
        if obj.is_active:
            ModelConfiguration.objects.exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)


@admin.register(ModelState)
class ModelStateAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['key', 'value']
    readonly_fields = ['updated_at']
    
    def has_add_permission(self, request):
        # Only allow editing existing state, not creating new entries
        return False


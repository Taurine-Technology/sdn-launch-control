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
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class ModelConfiguration(models.Model):
    """Database model for storing model configurations"""
    
    MODEL_TYPES = [
        ('keras_h5', 'Keras H5'),
        ('tensorflow_saved_model', 'TensorFlow SavedModel'),
        ('pytorch', 'PyTorch'),
        ('onnx', 'ONNX'),
    ]
    
    # Basic model info
    name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    model_type = models.CharField(max_length=50, choices=MODEL_TYPES)
    model_path = models.CharField(max_length=500)
    
    # Model parameters
    input_shape = models.JSONField(help_text="Input shape as JSON array, e.g., [225, 5]")
    num_categories = models.IntegerField()
    confidence_threshold = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # Metadata
    description = models.TextField(blank=True)
    version = models.CharField(max_length=50, default="1.0")
    is_active = models.BooleanField(default=False)
    is_loaded = models.BooleanField(default=False)
    
    # Categories (stored as JSON for flexibility)
    categories = models.JSONField(help_text="List of category names")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.display_name} ({self.name})"
    
    def save(self, *args, **kwargs):
        # Ensure only one model is active at a time
        if self.is_active:
            ModelConfiguration.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
    
    @property
    def input_dimensions(self):
        """Get input dimensions for reshaping"""
        if isinstance(self.input_shape, list):
            return self.input_shape
        return json.loads(self.input_shape) if isinstance(self.input_shape, str) else [225, 5]


class ModelState(models.Model):
    """Global model state management"""
    
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value}"
    
    @classmethod
    def get_value(cls, key, default=None):
        """Get a state value"""
        try:
            state = cls.objects.get(key=key)
            return state.value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_value(cls, key, value):
        """Set a state value"""
        state, created = cls.objects.get_or_create(key=key)
        state.value = value
        state.save()
        return state

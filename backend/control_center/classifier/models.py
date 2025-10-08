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


class ClassificationStats(models.Model):
    """Track classification statistics over time"""
    
    CONFIDENCE_TYPES = [
        ('HIGH', 'High Confidence'),
        ('LOW', 'Low Confidence'),
        ('MULTIPLE_CANDIDATES', 'Multiple Candidates'),
        ('UNCERTAIN', 'Uncertain'),
    ]
    
    # Link to model
    model_configuration = models.ForeignKey(
        ModelConfiguration,
        on_delete=models.CASCADE,
        related_name='classification_stats'
    )
    
    # Timestamp for this stats period
    timestamp = models.DateTimeField(db_index=True)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Total classifications in this period
    total_classifications = models.IntegerField(default=0)
    
    # Breakdown by confidence level
    high_confidence_count = models.IntegerField(default=0)
    low_confidence_count = models.IntegerField(default=0)
    multiple_candidates_count = models.IntegerField(default=0)
    uncertain_count = models.IntegerField(default=0)
    
    # DNS and other special detections
    dns_detections = models.IntegerField(default=0)
    asn_fallback_count = models.IntegerField(default=0)
    
    # Average prediction time
    avg_prediction_time_ms = models.FloatField(default=0.0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['model_configuration', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
        verbose_name_plural = 'Classification Statistics'
    
    def __str__(self):
        return f"{self.model_configuration.name} - {self.timestamp} ({self.total_classifications} classifications)"
    
    @property
    def high_confidence_percentage(self):
        """Calculate percentage of high confidence classifications"""
        if self.total_classifications == 0:
            return 0.0
        return (self.high_confidence_count / self.total_classifications) * 100
    
    @property
    def low_confidence_percentage(self):
        """Calculate percentage of low confidence classifications"""
        if self.total_classifications == 0:
            return 0.0
        return (self.low_confidence_count / self.total_classifications) * 100
    
    @property
    def multiple_candidates_percentage(self):
        """Calculate percentage of multiple candidates classifications"""
        if self.total_classifications == 0:
            return 0.0
        return (self.multiple_candidates_count / self.total_classifications) * 100
    
    @property
    def uncertain_percentage(self):
        """Calculate percentage of uncertain classifications"""
        if self.total_classifications == 0:
            return 0.0
        return (self.uncertain_count / self.total_classifications) * 100

# models.py
from django.db import models
from django.core.validators import RegexValidator
import hashlib

mac_address_validator = RegexValidator(
    regex=r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
    message="Enter a valid MAC address in format XX:XX:XX:XX:XX:XX."
)

class Flow(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    src_ip = models.GenericIPAddressField()
    dst_ip = models.GenericIPAddressField()
    src_mac = models.CharField(max_length=17, validators=[mac_address_validator],)
    dst_mac = models.CharField(max_length=17, blank=True, null=True, validators=[mac_address_validator],)
    src_port = models.PositiveIntegerField(blank=True, null=True)
    dst_port = models.PositiveIntegerField(blank=True, null=True)
    protocol = models.CharField(max_length=10, blank=True, null=True)
    classification = models.CharField(max_length=50)


    def __str__(self):
        return f"{self.timestamp}: {self.src_mac} -> {self.dst_mac} ({self.classification})"


class AggregatedFlow(models.Model):
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    classification = models.CharField(max_length=50)
    count = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.period_start:%Y-%m-%d %H:%M} - {self.classification}: {self.count}"

class FlowStat(models.Model):
    timestamp = models.DateTimeField()
    classification = models.CharField(max_length=255, db_index=True)
    meter_id = models.IntegerField(default=0)  # Meter ID actually applied by the flow

    duration_seconds = models.FloatField()
    packet_count = models.BigIntegerField()  # Can be large
    byte_count = models.BigIntegerField()  # Can be large
    priority = models.IntegerField()

    mac_address = models.CharField(max_length=17, blank=True, null=True)
    protocol = models.CharField(max_length=10, blank=True, null=True)
    port = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Stat @ {self.timestamp} for classification {self.classification}"

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['classification', 'timestamp']),
            models.Index(fields=['timestamp']),
            # TimescaleDB optimized indexes
            models.Index(fields=['mac_address', 'timestamp']),
            models.Index(fields=['protocol', 'timestamp']),
        ]
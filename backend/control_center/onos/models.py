from django.db import models
from general.models import Device
# Create your models here.
class Meter(models.Model):

    METER_TYPES = (
        ('drop', 'drop'),
    )
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='meter_controller')
    meter_id = models.IntegerField(unique=True)
    meter_type = models.CharField(max_length=30, choices=METER_TYPES)
    rate = models.IntegerField()
    switch_id = models.CharField(max_length=30)
    categories = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        unique_together = ('meter_type', 'rate', 'switch_id')

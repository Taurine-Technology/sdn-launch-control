from django.db import models

# Create your models here.
from general.models import Device, Bridge, Port


class Controller(models.Model):
    TYPES = (
        ('onos', 'Onos'),
        ('odl', 'Open Daylight'),
        ('other', 'Other')
    )
    type = models.CharField(max_length=20, choices=TYPES)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='controller')
    lan_ip_address = models.GenericIPAddressField(unique=True)

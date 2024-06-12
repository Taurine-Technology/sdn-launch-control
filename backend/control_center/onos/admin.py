from django.contrib import admin

# Register your models here.
from .models import Meter


@admin.register(Meter)
class MeterAdmin(admin.ModelAdmin):
    list_display = ('meter_id', 'switch_id', 'device')
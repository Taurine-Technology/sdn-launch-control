from django.contrib import admin

# Register your models here.
from django.contrib import admin

# Register your models here.
from .models import Controller


@admin.register(Controller)
class ControllerAdmin(admin.ModelAdmin):
    list_display = ('lan_ip_address', 'type', 'device')
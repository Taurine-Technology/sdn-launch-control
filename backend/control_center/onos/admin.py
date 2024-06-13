from django.contrib import admin

# Register your models here.
from .models import Meter, Category


@admin.register(Meter)
class MeterAdmin(admin.ModelAdmin):
    list_display = ('meter_id', 'switch_id', 'controller_device')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    display = ('name')
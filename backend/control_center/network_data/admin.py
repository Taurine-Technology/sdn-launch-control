from django.contrib import admin
from .models import Flow, AggregatedFlow, FlowStat

@admin.register(AggregatedFlow)
class AggregatedFlowAdmin(admin.ModelAdmin):
    list_display = ('period_start', 'period_end', 'classification', 'count')

@admin.register(Flow)
class FlowAdmin(admin.ModelAdmin):
    list_display = ('classification', 'src_mac', 'timestamp')

@admin.register(FlowStat)
class FlowStatAdmin(admin.ModelAdmin):
    list_display = ('classification', 'mac_address', 'timestamp', 'byte_count')
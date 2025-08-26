from django.contrib import admin
from .models import Notifier, Notification, NetworkSummaryNotification, DataUsageNotification, ApplicationUsageNotification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at', 'notifier')
    search_fields = ('user__username', 'message')
    list_filter = ('is_read', 'created_at')

@admin.register(Notifier)
class NotifierAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'chat_id', 'telegram_api_key')
    search_fields = ('user__username', 'phone_number', 'chat_id')

@admin.register(NetworkSummaryNotification)
class NetworkSummaryNotificationAdmin(admin.ModelAdmin):
    list_display = ('notifier', 'frequency', 'top_users_count', 'top_apps_count', 'celery_task_name')
    search_fields = ('notifier__user__username',)
    list_filter = ('frequency',)

@admin.register(DataUsageNotification)
class DataUsageNotificationAdmin(admin.ModelAdmin):
    list_display = ('notifier', 'frequency', 'data_limit_mb', 'celery_task_name')
    search_fields = ('notifier__user__username',)
    list_filter = ('frequency', 'data_limit_mb')


@admin.register(ApplicationUsageNotification)
class ApplicationUsageNotificationAdmin(admin.ModelAdmin):
    list_display = ('notifier', 'frequency', 'data_limit_mb', 'celery_task_name')
    search_fields = ('notifier__user__username',)
    list_filter = ('frequency', 'data_limit_mb')

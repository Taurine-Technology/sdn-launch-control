from django.db import models
from django.conf import settings
from django_celery_beat.models import PeriodicTask, PeriodicTasks, IntervalSchedule
import json

class Notifier(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=11, unique=True, blank=True, null=True)
    chat_id = models.CharField(max_length=50, unique=True)
    telegram_api_key = models.CharField(max_length=100)

    def __str__(self):
        return f"Notifier for {self.user.username} ({self.phone_number})"

class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    URGENCY_CHOICES = [
        ("low", "low"),
        ("medium", "medium"),
        ("high", "high"),
    ]
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default="medium")
    TYPE_CHOICES = [
        ("DEVICE_RESOURCE", "Device Resource"),
        ("NETWORK_SUMMARY", "Network Summary"),
        ("DATA_USAGE", "Data Usage"),
        ("APPLICATION_USAGE", "Application Usage"),
        ("OTHER", "Other"),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="OTHER", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    notifier = models.ForeignKey(Notifier, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            # Composite index for filtering by user and ordering by created_at
            models.Index(fields=["user", "-created_at"], name="notif_user_created_idx"),
            # Composite index for filtering by user, read status, and ordering
            models.Index(fields=["user", "is_read", "-created_at"], name="notif_user_read_created_idx"),
        ]

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:20]}"


class NetworkSummaryNotification(models.Model):
    FREQUENCY_CHOICES = [
        (1, "Every minute"),
        (10, "Every 10 minutes"),
        (60, "Every hour"),
        (360, "Every 6 hours"),
        (720, "Every 12 hours"),
        (1440, "Every 24 hours"),
    ]

    notifier = models.ForeignKey(Notifier, on_delete=models.CASCADE, related_name="network_summary_notifications")
    frequency = models.IntegerField(choices=FREQUENCY_CHOICES)
    top_users_count = models.PositiveIntegerField(default=5, help_text="Number of top users to display")
    top_apps_count = models.PositiveIntegerField(default=5, help_text="Number of top applications to display")
    celery_task_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.notifier.user.username} - Network Summary ({self.get_frequency_display()})"

    def schedule_notification_task(self):
        """
        Deletes old periodic task (if exists) and schedules a new one with updated values.
        """
        self.delete_notification_task()  # Ensure old task is removed

        schedule, created = IntervalSchedule.objects.get_or_create(
            every=self.frequency,
            period=IntervalSchedule.MINUTES
        )

        task_name = f"network_summary_{self.id}"
        task = PeriodicTask.objects.create(
            interval=schedule,
            name=task_name,
            task="notification.tasks.send_network_summary",
            args=json.dumps([self.id]),
        )

        self.celery_task_name = task_name  # Store task name
        self.save()

        # manually reload tasks
        # PeriodicTask.objects.update(last_run_at=None)
        PeriodicTasks.changed(task)

    def delete_notification_task(self):
        """
        Deletes the associated Celery Beat task if it exists.
        """
        if self.celery_task_name:
            try:
                task = PeriodicTask.objects.get(name=self.celery_task_name)
                task.delete()
                self.celery_task_name = None  # Clear reference
                self.save()
            except PeriodicTask.DoesNotExist:
                pass


class DataUsageNotification(models.Model):
    FREQUENCY_CHOICES = [
        (1, "Every minute"),
        (10, "Every 10 minutes"),
        (60, "Every hour"),
        (360, "Every 6 hours"),
        (720, "Every 12 hours"),
        (1440, "Every 24 hours"),
    ]

    notifier = models.ForeignKey(Notifier, on_delete=models.CASCADE, related_name="data_usage_notifications")
    frequency = models.IntegerField(choices=FREQUENCY_CHOICES)
    data_limit_mb = models.PositiveIntegerField(help_text="Data limit in MB")
    celery_task_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.notifier.user.username} - Data Usage Alert ({self.get_frequency_display()})"

    def schedule_notification_task(self):
        """
        Deletes old periodic task (if exists) and schedules a new one with updated values.
        """
        self.delete_notification_task()  # Ensure old task is removed

        schedule, created = IntervalSchedule.objects.get_or_create(
            every=self.frequency,
            period=IntervalSchedule.MINUTES
        )

        task_name = f"data_usage_alert_{self.id}"
        task = PeriodicTask.objects.create(
            interval=schedule,
            name=task_name,
            task="notification.tasks.check_data_usage",
            args=json.dumps([self.id]),
        )

        self.celery_task_name = task_name  # Store task name
        self.save()

        # manually reload tasks
        # PeriodicTask.objects.update(last_run_at=None)
        PeriodicTasks.changed(task)

    def delete_notification_task(self):
        """
        Deletes the associated Celery Beat task if it exists.
        """
        if self.celery_task_name:
            try:
                task = PeriodicTask.objects.get(name=self.celery_task_name)
                task.delete()
                self.celery_task_name = None  # Clear reference
                self.save()
            except PeriodicTask.DoesNotExist:
                pass


class ApplicationUsageNotification(models.Model):
    FREQUENCY_CHOICES = [
        (1, "Every minute"),
        (10, "Every 10 minutes"),
        (60, "Every hour"),
        (360, "Every 6 hours"),
        (720, "Every 12 hours"),
        (1440, "Every 24 hours"),
    ]

    notifier = models.ForeignKey(Notifier, on_delete=models.CASCADE, related_name="app_usage_notifications")
    frequency = models.IntegerField(choices=FREQUENCY_CHOICES)
    data_limit_mb = models.PositiveIntegerField(help_text="Data limit per application/category in MB")
    celery_task_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.notifier.user.username} - App Usage Alert ({self.get_frequency_display()})"

    def schedule_notification_task(self):
        """
        Deletes old periodic task (if exists) and schedules a new one with updated values.
        """
        self.delete_notification_task()  # Ensure old task is removed

        schedule, created = IntervalSchedule.objects.get_or_create(
            every=self.frequency,
            period=IntervalSchedule.MINUTES
        )

        task_name = f"app_usage_alert_{self.id}"
        task = PeriodicTask.objects.create(
            interval=schedule,
            name=task_name,
            task="notification.tasks.check_application_usage",
            args=json.dumps([self.id]),
        )

        self.celery_task_name = task_name  # Store task name
        self.save()

        # manually reload tasks
        # PeriodicTask.objects.update(last_run_at=None)
        PeriodicTasks.changed(task)


    def delete_notification_task(self):
        """
        Deletes the associated Celery Beat task if it exists.
        """
        if self.celery_task_name:
            try:
                task = PeriodicTask.objects.get(name=self.celery_task_name)
                task.delete()
                self.celery_task_name = None  # Clear reference
                self.save()
            except PeriodicTask.DoesNotExist:
                pass

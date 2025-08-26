from rest_framework import serializers
from .models import Notification, Notifier, NetworkSummaryNotification, DataUsageNotification, ApplicationUsageNotification


class NotifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifier
        fields = ['id', 'user', 'phone_number', 'chat_id', 'telegram_api_key']


class NotificationSerializer(serializers.ModelSerializer):
    # This field displays the chat_id from the related notifier (if one exists)
    notifier_chat_id = serializers.CharField(source='notifier.chat_id', read_only=True, default=None)

    class Meta:
        model = Notification
        fields = ['id', 'user', 'message', 'is_read', 'created_at', 'notifier', 'notifier_chat_id']
        read_only_fields = ['id', 'created_at']


class NetworkSummaryNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkSummaryNotification
        fields = ["id", "frequency", "top_users_count", "top_apps_count"]  # Exclude `notifier`

    def create(self, validated_data):
        """
        Custom create method to ensure `notifier` is automatically assigned.
        """
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError({"error": "User must be authenticated."})

        try:
            notifier = request.user.notifier
        except AttributeError:
            raise serializers.ValidationError({"error": "Notifier for this user does not exist."})

        validated_data["notifier"] = notifier
        notification = NetworkSummaryNotification.objects.create(**validated_data)
        notification.schedule_notification_task()
        return notification

    def update(self, instance, validated_data):
        """
        Handles updating the notification, ensuring the periodic task is recreated.
        """
        instance.delete_notification_task()  # Remove old task

        # Update fields
        instance.frequency = validated_data.get("frequency", instance.frequency)
        instance.top_users_count = validated_data.get("top_users_count", instance.top_users_count)
        instance.top_apps_count = validated_data.get("top_apps_count", instance.top_apps_count)
        instance.save()

        instance.schedule_notification_task()  # Recreate task with new values
        return instance


class DataUsageNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataUsageNotification
        fields = ["id", "frequency", "data_limit_mb"]

    def create(self, validated_data):
        """
        Custom create method to ensure `notifier` is automatically assigned.
        """
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError({"error": "User must be authenticated."})

        try:
            notifier = request.user.notifier
        except AttributeError:
            raise serializers.ValidationError({"error": "Notifier for this user does not exist."})

        validated_data["notifier"] = notifier
        notification = DataUsageNotification.objects.create(**validated_data)
        notification.schedule_notification_task()
        return notification

    def update(self, instance, validated_data):
        instance.delete_notification_task()  # Remove old task

        instance.frequency = validated_data.get("frequency", instance.frequency)
        instance.data_limit_mb = validated_data.get("data_limit_mb", instance.data_limit_mb)
        instance.save()

        instance.schedule_notification_task()  # Recreate task with new values
        return instance


class ApplicationUsageNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationUsageNotification
        fields = ["id", "frequency", "data_limit_mb"]

    def create(self, validated_data):
        """
        Custom create method to ensure `notifier` is automatically assigned.
        """
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError({"error": "User must be authenticated."})

        try:
            notifier = request.user.notifier
        except AttributeError:
            raise serializers.ValidationError({"error": "Notifier for this user does not exist."})

        validated_data["notifier"] = notifier
        notification = ApplicationUsageNotification.objects.create(**validated_data)
        notification.schedule_notification_task()
        return notification

    def update(self, instance, validated_data):
        instance.delete_notification_task()  # Remove old task

        instance.frequency = validated_data.get("frequency", instance.frequency)
        instance.data_limit_mb = validated_data.get("data_limit_mb", instance.data_limit_mb)
        instance.save()

        instance.schedule_notification_task()  # Recreate task with new values
        return instance
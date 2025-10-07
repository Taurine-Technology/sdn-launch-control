from rest_framework import serializers
from .models import Notification


class NetworkNotificationUISerializer(serializers.ModelSerializer):
    # Map backend fields to UI contract
    read = serializers.BooleanField(source="is_read")
    type = serializers.SerializerMethodField()
    description = serializers.CharField(source="message")
    user = serializers.SerializerMethodField()
    urgency = serializers.CharField(required=False)

    class Meta:
        model = Notification
        fields = ["id", "read", "type", "description", "user", "urgency", "created_at"]

    def get_type(self, obj: Notification) -> str:
        # Default type until categorization is added
        """
        Provide the notification type string for UI consumption.
        
        Parameters:
            obj (Notification): The Notification instance being serialized.
        
        Returns:
            str: The notification type value. Returns "OTHER" as the default type until notifications are categorized.
        """
        return "OTHER"

    def get_user(self, obj: Notification):
        # Optional surface of notifier information if available
        """
        Return the notifier's chat ID for a notification when available.
        
        Parameters:
            obj (Notification): Notification instance from which to retrieve the notifier.
        
        Returns:
            str or None: The notifier's `chat_id` if a notifier exists and can be accessed, otherwise `None`.
        """
        try:
            return obj.notifier.chat_id if obj.notifier else None
        except Exception:
            return None


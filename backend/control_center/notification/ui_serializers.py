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
        Map a Notification instance to a UI-facing notification type string.
        
        Returns:
            str: Notification type code; currently always "OTHER".
        """
        return "OTHER"

    def get_user(self, obj: Notification):
        # Optional surface of notifier information if available
        """
        Return the notifier's chat_id for the given notification if available.
        
        Parameters:
            obj (Notification): Notification instance from which to extract notifier information.
        
        Returns:
            str or None: The notifier's `chat_id` if a notifier is present and accessible, otherwise `None`.
        """
        try:
            return obj.notifier.chat_id if obj.notifier else None
        except Exception:
            return None


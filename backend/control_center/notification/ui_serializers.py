from rest_framework import serializers
from .models import Notification


class NetworkNotificationUISerializer(serializers.ModelSerializer):
    # Map backend fields to UI contract
    read = serializers.BooleanField(source="is_read")
    type = serializers.SerializerMethodField()
    description = serializers.CharField(source="message")
    user = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ["id", "read", "type", "description", "user", "created_at"]

    def get_type(self, obj: Notification) -> str:
        # Default type until categorization is added
        return "OTHER"

    def get_user(self, obj: Notification):
        # Optional surface of notifier information if available
        try:
            return obj.notifier.chat_id if obj.notifier else None
        except Exception:
            return None



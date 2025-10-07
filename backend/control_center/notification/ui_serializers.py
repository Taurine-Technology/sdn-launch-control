from rest_framework import serializers
from .models import Notification


class NetworkNotificationUISerializer(serializers.ModelSerializer):
    # Map backend fields to UI contract
    read = serializers.BooleanField(source="is_read", required=False)
    type = serializers.SerializerMethodField()
    description = serializers.CharField(source="message")
    user = serializers.SerializerMethodField(read_only=True)
    urgency = serializers.CharField(required=False)

    class Meta:
        model = Notification
        fields = ["id", "read", "type", "description", "user", "urgency", "created_at"]
        read_only_fields = ["id", "created_at", "type"]

    def get_type(self, obj: Notification) -> str:
        # Default type until categorization is added
        return "OTHER"

    def get_user(self, obj: Notification):
        # Return the username of the user who owns this notification
        try:
            return obj.user.username if obj.user else None
        except Exception:
            return None
    
    def create(self, validated_data):
        # Automatically set the user from the request context
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["user"] = request.user
        return super().create(validated_data)



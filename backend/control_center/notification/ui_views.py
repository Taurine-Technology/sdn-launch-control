from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.fields import BooleanField

from .models import Notification
from .ui_serializers import NetworkNotificationUISerializer


class NetworkNotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NetworkNotificationUISerializer

    def get_queryset(self):
        """
        Return notifications for the authenticated user, optionally filtered by read status.
        
        If the request includes a "read" query parameter with value "true" or "false" (case-insensitive),
        the result is filtered to only read or only unread notifications respectively.
        
        Returns:
            QuerySet: Notification objects for the current user, ordered by `created_at` descending; when applicable, restricted to read or unread notifications based on the "read" query parameter.
        """
        qs = Notification.objects.filter(user=self.request.user).order_by("-created_at")
        read = self.request.query_params.get("read")
        if read is not None:
            if read.lower() == "true":
                qs = qs.filter(is_read=True)
            elif read.lower() == "false":
                qs = qs.filter(is_read=False)
        return qs

    def partial_update(self, request, *args, **kwargs):
        # Support { read: true } mapping to is_read
        """
        Apply allowed partial updates to the targeted Notification and return its serialized representation.
        
        Supports updating the notification's read state via the `read` field and the urgency via the `urgency` field (accepted values: "low", "medium", "high"). If either field differs from the current value the instance is saved before serialization.
        
        Returns:
            dict: Serialized notification data after applying updates.
        
        Notes:
            If `read` is provided but cannot be parsed as a boolean, the view returns an HTTP 400 response with an `{"error": "Invalid read value"}` payload.
        """
        instance = self.get_object()
        read_val = request.data.get("read")
        urgency = request.data.get("urgency")
        changed = False
        if read_val is not None:
            try:
                parsed = BooleanField().to_internal_value(read_val)
            except Exception:
                return Response({"error": "Invalid read value"}, status=status.HTTP_400_BAD_REQUEST)
            if instance.is_read != parsed:
                instance.is_read = parsed
                changed = True
        if urgency:
            val = urgency.lower()
            if val in ("low", "medium", "high") and val != instance.urgency:
                instance.urgency = val
                changed = True
        if changed:
            instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
        
    def create(self, request, *args, **kwargs):
        # Allow creating simple notifications for the current user
        """
        Create a Notification for the authenticated user using request data.
        
        Uses 'description' or 'message' from request.data as the notification content. The 'urgency' field defaults to "medium" and is constrained to "low", "medium", or "high"; invalid values default to "medium". If no message is provided, a 400 error response is returned.
        
        Returns:
        	Serialized data of the created Notification.
        """
        message = request.data.get("description") or request.data.get("message")
        urgency = request.data.get("urgency", "medium")
        if not message:
            return Response({"error": "description is required"}, status=status.HTTP_400_BAD_REQUEST)
        if urgency not in ("low", "medium", "high"):
            urgency = "medium"
        n = Notification.objects.create(user=request.user, message=message, urgency=urgency)
        serializer = self.get_serializer(n)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="read/all")
    def mark_all_read(self, request):
        """
        Mark all unread notifications for the authenticated user as read.
        
        Returns:
            updated (int): Number of notifications that were marked as read.
        """
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"updated": updated}, status=status.HTTP_200_OK)


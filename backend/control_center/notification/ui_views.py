from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification
from .ui_serializers import NetworkNotificationUISerializer


class NetworkNotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing network notifications.
    
    Provides full CRUD operations with automatic field mapping via the serializer:
    - UI 'read' field maps to backend 'is_read'
    - UI 'description' field maps to backend 'message'
    - UI 'user' field automatically returns username (read-only)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NetworkNotificationUISerializer

    def get_queryset(self):
        """
        Filter notifications to current user only, ordered by newest first.
        Supports optional 'read' query parameter to filter by read status.
        """
        qs = Notification.objects.filter(user=self.request.user).order_by("-created_at")
        read = self.request.query_params.get("read")
        if read is not None:
            if read.lower() == "true":
                qs = qs.filter(is_read=True)
            elif read.lower() == "false":
                qs = qs.filter(is_read=False)
        return qs

    @action(detail=False, methods=["post"], url_path="read/all")
    def mark_all_read(self, request):
        """
        Custom action to mark all unread notifications as read.
        Endpoint: POST /network-notifications/read/all/
        """
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"updated": updated}, status=status.HTTP_200_OK)



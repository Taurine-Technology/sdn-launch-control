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
        Return notifications for the authenticated user ordered by newest first.
        
        If the optional `read` query parameter is provided with the value `"true"` or `"false"` (case-insensitive),
        the queryset is further filtered to notifications with `is_read = True` or `is_read = False` respectively.
        
        Parameters:
            None (reads optional `read` from `self.request.query_params`)
        
        Returns:
            QuerySet: Notification objects for `self.request.user`, optionally filtered by `is_read`, ordered by `-created_at`.
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
        Mark all unread notifications for the authenticated user as read.
        
        Returns:
            updated (int): Number of notifications that were updated to read.
        """
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"updated": updated}, status=status.HTTP_200_OK)


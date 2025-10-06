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
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"updated": updated}, status=status.HTTP_200_OK)



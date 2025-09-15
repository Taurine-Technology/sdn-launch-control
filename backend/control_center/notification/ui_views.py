from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
        if read_val is not None:
            instance.is_read = bool(read_val)
            instance.save(update_fields=["is_read"])
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=["post"], url_path="read/all")
    def mark_all_read(self, request):
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"updated": updated}, status=status.HTTP_200_OK)



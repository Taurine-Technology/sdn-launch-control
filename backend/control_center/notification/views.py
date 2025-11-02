# notification/views.py
from .tasks import monitor_telegram_registration
import json
import logging
import requests
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import DataUsageNotificationSerializer
from .models import Notification, Notifier, NetworkSummaryNotification, DataUsageNotification, ApplicationUsageNotification
from .serializers import NotificationSerializer, NetworkSummaryNotificationSerializer, ApplicationUsageNotificationSerializer

logger = logging.getLogger(__name__)

class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows notifications to be viewed or edited.
    Returns notifications only for the authenticated user.
    """
    serializer_class = NotificationSerializer


    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class TelegramTestView(APIView):
    """
    A simple test view to send a test message via the Telegram API using the user’s Notifier.
    """


    def get(self, request, format=None):
        # Retrieve the notifier for the authenticated user.
        try:
            notifier = request.user.notifier
        except Notifier.DoesNotExist:
            return Response(
                {'error': 'Notifier for this user does not exist. Please create one.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        telegram_api_key = getattr(settings, 'TELEGRAM_API_KEY', None)
        if not telegram_api_key:
            return Response(
                {'error': 'TELEGRAM_API_KEY not set in settings'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        telegram_url = f"https://api.telegram.org/bot{telegram_api_key}/sendMessage"
        data = {
            'chat_id': notifier.chat_id,
            'text': "Test notification from Django API"
        }
        response = requests.post(telegram_url, data=data)
        if response.status_code == 200:
            return Response({'status': 'Message sent', 'response': response.json()})
        else:
            return Response(
                {'error': 'Failed to send message', 'details': response.text},
                status=response.status_code
            )


class LinkTelegramView(APIView):
    """
    Starts a Celery task to monitor Telegram messages for the linking process.
    """


    def post(self, request):
        try:
            data = json.loads(request.body)
            unique_token = data.get("unique_token")

            if not unique_token:
                return Response({"error": "Missing unique token"}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the user already has a notifier
            if Notifier.objects.filter(user=request.user).exists():
                return Response({"error": "Telegram already linked"}, status=status.HTTP_400_BAD_REQUEST)

            # Start Celery task
            monitor_telegram_registration.delay(request.user.id, unique_token)

            return Response({"message": "Started Telegram linking process"}, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NetworkSummaryNotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing network summary notification settings.
    """
    serializer_class = NetworkSummaryNotificationSerializer


    def get_queryset(self):
        return NetworkSummaryNotification.objects.filter(notifier__user=self.request.user)

    def perform_create(self, serializer):
        logger.debug("perform_create with", self.request.user)

        # Ensure that `request` context is passed to serializer
        serializer.save()


    def perform_destroy(self, instance):
        instance.delete_notification_task()
        instance.delete()

class DataUsageNotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing data usage notifications.
    """
    serializer_class = DataUsageNotificationSerializer

    def get_queryset(self):
        return DataUsageNotification.objects.filter(notifier__user=self.request.user)

    def perform_create(self, serializer):
        notifier, created = Notifier.objects.get_or_create(user=self.request.user)
        serializer.save(notifier=notifier)

    def perform_destroy(self, instance):
        instance.delete_notification_task()
        instance.delete()

class ApplicationUsageNotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing application usage notifications.
    """
    serializer_class = ApplicationUsageNotificationSerializer

    def get_queryset(self):
        return ApplicationUsageNotification.objects.filter(notifier__user=self.request.user)

    def perform_create(self, serializer):
        notifier, created = Notifier.objects.get_or_create(user=self.request.user)
        serializer.save(notifier=notifier)

    def perform_destroy(self, instance):
        instance.delete_notification_task()
        instance.delete()

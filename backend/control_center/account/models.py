# models.py

from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    telegram_username = models.CharField(max_length=150, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    telegram_linked = models.BooleanField(default=False)
    telegram_chat_id = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return self.user.username


class Account(models.Model):
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    surname = models.CharField(max_length=100, blank=True, null=True)
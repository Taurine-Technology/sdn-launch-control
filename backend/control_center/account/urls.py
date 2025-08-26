from django.urls import path
from .views import UserProfileUpdateView, ChangePasswordView, RefreshTokenView, Test401View

app_name = 'account'

urlpatterns = [
    path('account/test-401/', Test401View.as_view(), name='test-401'),
    path('account/refresh-token/', RefreshTokenView.as_view(), name='refresh-token'),
    path('account/profile/', UserProfileUpdateView.as_view(), name="profile"),
    path('account/change-password/', ChangePasswordView.as_view(), name="change-password"),
]

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .serializers import UserSerializer, ChangePasswordSerializer, UserProfileSerializer
from knox.auth import TokenAuthentication
from rest_framework import status
# views.py
from knox.models import AuthToken

# API View for Profile
class UserProfileUpdateView(APIView):

    def get(self, request):
        user_serializer = UserSerializer(request.user)
        profile_serializer = UserProfileSerializer(request.user.profile)
        return Response({
            "user": user_serializer.data,
            "profile": profile_serializer.data
        })

    def put(self, request):
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        profile_serializer = UserProfileSerializer(request.user.profile, data=request.data, partial=True)

        if user_serializer.is_valid() and profile_serializer.is_valid():
            user_serializer.save()
            profile_serializer.save()
            return Response({"message": "Profile updated successfully"})
        return Response({"errors": user_serializer.errors or profile_serializer.errors}, status=400)


# API View for Changing Password
class ChangePasswordView(APIView):

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            if not request.user.check_password(serializer.validated_data["old_password"]):
                return Response({"error": "Old password is incorrect"}, status=400)

            request.user.set_password(serializer.validated_data["new_password"])
            request.user.save()
            return Response({"message": "Password updated successfully"})

        return Response(serializer.errors, status=400)


class RefreshTokenView(APIView):
    def post(self, request, *args, **kwargs):
        user = request.user

        # Create a new token (this generates a new expiry automatically)
        instance, token = AuthToken.objects.create(user)

        # Optionally, delete the old token here if you want a one-to-one mapping

        return Response({
            "token": token,
            "expiry": instance.expiry  # instance.expiry is a datetime
        })

class Test401View(APIView):
    """
    A simple view that returns a 401 Unauthorized response.
    This can be used to simulate a session expiry.
    """
    def get(self, request, *args, **kwargs):
        return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
from django.contrib.auth.signals import user_logged_in, user_logged_out
from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.settings import knox_settings

UserSerializer = knox_settings.USER_SERIALIZER

class LoginView(APIView):
    authentication_classes = knox_settings.LOGIN_AUTHENTICATION_CLASSES
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        token = AuthToken.objects.create(request.user)
        user_logged_in.send(sender=request.user.__class__, request=request, user=request.user)
        return Response({
            "user": UserSerializer(request.user).data,
            "token": token,
        })

class LogoutView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        request._auth.delete()
        user_logged_out.send(sender=request.user.__class__, request=request, user=request.user)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

class LogoutAllView(APIView):
    '''
    Log the user out of all sessions
    I.E. deletes all auth tokens for the user
    '''
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        request.user.auth_token_set.all().delete()
        user_logged_out.send(sender=request.user.__class__, request=request, user=request.user)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

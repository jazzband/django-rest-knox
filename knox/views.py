from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from knox import crypto
from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.serializers import UserSerializer
from knox.settings import knox_settings

class LoginView(APIView):
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        token = self.create_and_save_token(request.user)
        return Response({
            "user": UserSerializer(request.user).data,
            "token": token,
        })

    def create_and_save_token(self, user):
        token = crypto.create_token_string()
        salt = crypto.create_salt_string()
        digest = crypto.hash_token(token, salt)
        auth_token = AuthToken(digest=digest, salt=salt, user=user)
        auth_token.save()
        return token

class LogoutView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        request._auth.delete()
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
        return Response(None, status=status.HTTP_204_NO_CONTENT)

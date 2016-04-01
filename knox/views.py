from datetime import timedelta

from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.settings import knox_settings
from knox.serializers import ExpirySerializer


UserSerializer = knox_settings.USER_SERIALIZER


class LoginView(APIView):
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        expiry_serializer = ExpirySerializer(data=self.request.query_params.dict())
        if  not expiry_serializer.is_valid():
            return Response(expiry_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token = AuthToken.objects.create(request.user, **dict(expiry_serializer.validated_data))
        return Response({
            "user": UserSerializer(request.user).data,
            "token": token,
        })


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

from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.serializers import UserSerializer

class LoginView(APIView):
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        token = AuthToken(user=request.user)
        token.save()
        return Response({
            "user": UserSerializer(request.user).data,
            "token": token.key,
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

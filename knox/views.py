from django.contrib.auth.signals import user_logged_in, user_logged_out
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.serializers import TokenSerializer
from knox.settings import knox_settings


class LoginView(APIView):
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        token = AuthToken.objects.create(request.user)
        user_logged_in.send(sender=request.user.__class__, request=request, user=request.user)
        UserSerializer = knox_settings.USER_SERIALIZER
        context = {'request': self.request, 'format': self.format_kwarg, 'view': self}
        return Response({
            'user': UserSerializer(request.user, context=context).data,
            'token': token,
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


class BaseJSONAuthenticationView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, *args, **kwargs):

        serializer = TokenSerializer(
            data=request.data
        )
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token = AuthToken.objects.create(user)
            return Response({'token': token})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JSONAuthenticationView(BaseJSONAuthenticationView):

    serializer_class = TokenSerializer


obtain_token = JSONAuthenticationView.as_view()

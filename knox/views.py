from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import DateTimeField
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from knox.auth import TokenAuthentication
from knox.models import get_token_model
from knox.settings import knox_settings


class LoginView(APIView):
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = (IsAuthenticated,)

    def get_context(self):
        return {'request': self.request, 'format': self.format_kwarg, 'view': self}

    def get_token_ttl(self):
        return knox_settings.TOKEN_TTL

    def get_token_prefix(self):
        return knox_settings.TOKEN_PREFIX

    def get_token_limit_per_user(self):
        return knox_settings.TOKEN_LIMIT_PER_USER

    def get_user_serializer_class(self):
        return knox_settings.USER_SERIALIZER

    def get_expiry_datetime_format(self):
        return knox_settings.EXPIRY_DATETIME_FORMAT

    def format_expiry_datetime(self, expiry):
        datetime_format = self.get_expiry_datetime_format()
        return DateTimeField(format=datetime_format).to_representation(expiry)

    def create_token(self):
        token_prefix = self.get_token_prefix()
        return get_token_model().objects.create(
            user=self.request.user, expiry=self.get_token_ttl(), prefix=token_prefix
        )

    def get_post_response_data(self, request, token, instance):
        UserSerializer = self.get_user_serializer_class()

        data = {
            'expiry': self.format_expiry_datetime(instance.expiry),
            'token': token
        }
        if UserSerializer is not None:
            data["user"] = UserSerializer(
                request.user,
                context=self.get_context()
            ).data
        return data

    def get_post_response(self, request, token, instance):
        data = self.get_post_response_data(request, token, instance)
        return Response(data)

    def post(self, request, format=None):
        token_limit_per_user = self.get_token_limit_per_user()
        if token_limit_per_user is not None:
            now = timezone.now()
            token = request.user.auth_token_set.filter(expiry__gt=now)
            if token.count() >= token_limit_per_user:
                return Response(
                    {"error": "Maximum amount of tokens allowed per user exceeded."},
                    status=status.HTTP_403_FORBIDDEN
                )
        instance, token = self.create_token()
        user_logged_in.send(sender=request.user.__class__,
                            request=request, user=request.user)
        return self.get_post_response(request, token, instance)


class LogoutView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_post_response(self, request):
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    def post(self, request, format=None):
        request._auth.delete()
        user_logged_out.send(sender=request.user.__class__,
                             request=request, user=request.user)
        return self.get_post_response(request)


class LogoutAllView(APIView):
    '''
    Log the user out of all sessions
    I.E. deletes all auth tokens for the user
    '''
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_post_response(self, request):
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    def post(self, request, format=None):
        request.user.auth_token_set.all().delete()
        user_logged_out.send(sender=request.user.__class__,
                             request=request, user=request.user)
        return self.get_post_response(request)

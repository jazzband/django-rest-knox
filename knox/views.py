from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import exceptions, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import DateTimeField
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from knox.auth import TokenAuthentication
from knox.models import (
    get_refresh_family_model, get_refresh_token_model, get_token_model,
)
from knox.serializers import RefreshTokenSerializer
from knox.settings import CONSTANTS, knox_settings


class LoginView(APIView):
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = (IsAuthenticated,)

    def get_context(self):
        return {"request": self.request, "format": self.format_kwarg, "view": self}

    def get_token_ttl(self):
        return knox_settings.TOKEN_TTL

    def get_token_prefix(self):
        return knox_settings.TOKEN_PREFIX

    def get_token_limit_per_user(self):
        return knox_settings.TOKEN_LIMIT_PER_USER

    def get_refresh_token_ttl(self):
        return knox_settings.REFRESH_TOKEN_TTL

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

    def create_refresh_token(self):
        return get_refresh_token_model().objects.create(
            user=self.request.user,
            expiry=self.get_refresh_token_ttl(),
        )

    def create_refresh_family(self, parent, refresh_token, token):
        return get_refresh_family_model().objects.create(
            user=self.request.user,
            parent=parent,
            refresh_token=refresh_token,
            token=token,
        )

    def get_post_response_data(self, request, token, instance):
        UserSerializer = self.get_user_serializer_class()
        data = {
            "expiry": self.format_expiry_datetime(instance.expiry),
            "token": token,
        }
        if UserSerializer is not None:
            data["user"] = UserSerializer(request.user, context=self.get_context()).data

        if knox_settings.ENABLE_REFRESH_TOKEN:
            return self.add_refresh_token(data, token)
        return data

    def add_refresh_token(self, data, token):
        refresh_instance, refresh_token = self.create_refresh_token()
        self.create_refresh_family(
            parent=refresh_token, refresh_token=refresh_token, token=token
        )
        data["refresh_token"] = refresh_token
        data["refresh_token_expiry"] = self.format_expiry_datetime(
            refresh_instance.expiry
        )
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
                    status=status.HTTP_403_FORBIDDEN,
                )

            if knox_settings.ENABLE_REFRESH_TOKEN:
                refresh_token = request.user.refresh_token_set.filter(expiry__gt=now)
                if refresh_token.count() >= token_limit_per_user:
                    return Response(
                        {
                            "error": "Maximum amount of tokens allowed per user exceeded."
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

        instance, token = self.create_token()
        user_logged_in.send(
            sender=request.user.__class__, request=request, user=request.user
        )
        return self.get_post_response(request, token, instance)


class RefreshTokenView(LoginView, TokenAuthentication):
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

    token_model = get_token_model()
    refresh_token_model = get_refresh_token_model()
    refresh_family_model = get_refresh_family_model()

    def get_post_response_data(self, token, instance, parent):
        data = {
            "expiry": self.format_expiry_datetime(instance.expiry),
            "token": token,
        }
        return self.add_refresh_token(data, token, parent)

    def add_refresh_token(self, data, token, parent):
        refresh_instance, refresh_token = self.create_refresh_token()
        self.create_refresh_family(
            parent=parent, refresh_token=refresh_token, token=token
        )
        data["refresh_token"] = refresh_token
        data["refresh_token_expiry"] = self.format_expiry_datetime(
            refresh_instance.expiry
        )
        return data

    def validate_member(self, refresh_token):
        member = self.refresh_family_model.objects.filter(
            refresh_token=refresh_token[: CONSTANTS.TOKEN_KEY_LENGTH]
        ).first()
        if member is None:
            return None, None
        family = self.refresh_family_model.objects.filter(parent=member.parent)
        newest_member = family.order_by("created").last()
        return family, newest_member

    def cleanup_history(self, family):
        token_history_limit = knox_settings.MAX_TOKEN_HISTORY
        if token_history_limit < 1:
            token_history_limit = 1
        if family.count() >= token_history_limit:
            ordered_queryset = family.order_by("-created")
            cutoff_entry = ordered_queryset[token_history_limit - 1]
            cutoff_entry_timestamp = cutoff_entry.created
            family.filter(created__lt=cutoff_entry_timestamp).delete()

    def delete_old_tokens(self, family):
        for token in family:
            self.token_model.objects.filter(token_key=token.token).delete()
            self.refresh_token_model.objects.filter(
                token_key=token.refresh_token
            ).delete()

    def post(self, request, format=None):
        serializer = RefreshTokenSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            refresh_token = validated_data["refresh_token"]

            family, newest_member = self.validate_member(refresh_token)

            if family is None or newest_member is None:
                raise exceptions.AuthenticationFailed(_("Invalid token."))

            delta = timezone.now() - newest_member.created
            if delta > knox_settings.MIN_REFRESH_TOKEN_ISSUE_INTERVAL:
                if (
                    newest_member.refresh_token
                    == refresh_token[: CONSTANTS.TOKEN_KEY_LENGTH]
                ):
                    user, token = self.authenticate_refresh_token(refresh_token)
                    if user:
                        self.request.user = user
                        self.delete_old_tokens(family)

                        new_token_instance, new_token = self.create_token()
                        data = self.get_post_response_data(
                            token=new_token,
                            instance=new_token_instance,
                            parent=newest_member.parent,
                        )
                        self.cleanup_history(family=family)
                        return Response(data)

                    # auth failed
                    raise exceptions.AuthenticationFailed(_("Invalid token."))
                # not newest
                for member in family:
                    self.token_model.objects.filter(token_key=member.token).delete()
                    self.refresh_token_model.objects.filter(
                        token_key=member.refresh_token
                    ).delete()
                family.delete()
                raise exceptions.AuthenticationFailed(_("Invalid token."))
            raise exceptions.Throttled()

        raise exceptions.AuthenticationFailed(_("Invalid token."))


class LogoutView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_post_response(self, request):
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    def post(self, request, format=None):
        token = request._auth
        if knox_settings.ENABLE_REFRESH_TOKEN:
            refresh_family_model = get_refresh_family_model()
            refresh_token_model = get_refresh_token_model()
            auth_token_model = get_token_model()

            parent = (
                refresh_family_model.objects.filter(token=token.token_key)
                .first()
                .parent
            )
            family = refresh_family_model.objects.filter(parent=parent)
            for token in family:
                auth_token_model.objects.filter(token_key=token.token).delete()
                refresh_token_model.objects.filter(
                    token_key=token.refresh_token
                ).delete()
            family.delete()
        else:
            token.delete()

        user_logged_out.send(
            sender=request.user.__class__, request=request, user=request.user
        )
        return self.get_post_response(request)


class LogoutAllView(APIView):
    """
    Log the user out of all sessions
    I.E. deletes all auth tokens for the user
    """

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_post_response(self, request):
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    def post(self, request, format=None):
        request.user.auth_token_set.all().delete()
        if knox_settings.ENABLE_REFRESH_TOKEN:
            request.user.refresh_token_set.all().delete()
            request.user.refresh_family_set.all().delete()

        user_logged_out.send(
            sender=request.user.__class__, request=request, user=request.user
        )
        return self.get_post_response(request)

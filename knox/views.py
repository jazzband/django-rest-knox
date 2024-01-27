try:
    from hmac import compare_digest
except ImportError:
    def compare_digest(a, b):
        return a == b

import binascii

from django.contrib.auth import settings
from knox.crypto import hash_token

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.response import Response
from rest_framework.serializers import DateTimeField
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework import exceptions
from knox.serializers import RefreshTokenSerializer
from knox.settings import CONSTANTS, knox_settings

from knox.models import get_refresh_family_model,get_refresh_token_model
from knox.auth import TokenAuthentication
from knox.models import get_token_model 
from knox.settings import knox_settings
from knox.signals import token_expired,refresh_token_expired

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
            user=self.request.user, expiry=self.get_refresh_token_ttl(),
        )
    
    def create_refresh_family(self,parent,refresh_token,token):
        return get_refresh_family_model().objects.create(user=self.request.user,parent=parent,refresh_token=refresh_token,token=token)



    def get_post_response_data(self, request, token, instance):
        UserSerializer = self.get_user_serializer_class()
        data = {
            'expiry': self.format_expiry_datetime(instance.expiry),
            'token': token,
        }
        if UserSerializer is not None:
            data["user"] = UserSerializer(
                request.user,
                context=self.get_context()
            ).data

        if knox_settings.ENABLE_REFRESH_TOKEN:
                        return self.add_refresh_token(data,token)
        return data

    def add_refresh_token(self,data,token):
        refresh_instance,refresh_token = self.create_refresh_token()
        self.create_refresh_family(parent=refresh_token,refresh_token=refresh_token,token=token) 
        data['refresh_token'] = refresh_token
        data['refresh_token_expiry'] = self.format_expiry_datetime(refresh_instance.expiry)
        return data


    def get_post_response(self, request, token, instance):
        data = self.get_post_response_data(request, token, instance)
        return Response(data)

    def post(self, request, format=None):
        token_limit_per_user = self.get_token_limit_per_user()
        if token_limit_per_user is not None:
            now = timezone.now()
            token = request.user.auth_token_set.filter(expiry__gt=now)
            if knox_settings.ENABLE_REFRESH_TOKEN:
                    refresh_token = request.user.refresh_token_set.filter(expiry__gt=now)
                    if refresh_token.count() >= token_limit_per_user:
                            return Response(
                    {"error": "Maximum amount of tokens allowed per user exceeded."},
                    status=status.HTTP_403_FORBIDDEN
                )
 
            if token.count() >= token_limit_per_user:
                return Response(
                    {"error": "Maximum amount of tokens allowed per user exceeded."},
                    status=status.HTTP_403_FORBIDDEN
                )
        instance, token = self.create_token()
        user_logged_in.send(sender=request.user.__class__,
                            request=request, user=request.user)
        return self.get_post_response(request, token, instance)


class RefreshTokenView(LoginView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]

   
    def get_post_response_data(self, token, instance,refresh_token,refresh_token_instance):
        data = {
            'expiry': self.format_expiry_datetime(instance.expiry),
            'token': token,
            'refresh_token': refresh_token,
            'refresh_token_expiry': self.format_expiry_datetime(refresh_token_instance.expiry)
        }
        return data
    

    def post(self, request, format=None):

        serializer =  RefreshTokenSerializer(data=request.data)
        if serializer.is_valid():
            # Access the validated data
            validated_data = serializer.validated_data
            refresh_token = validated_data['refresh_token']

            refresh_family_model = get_refresh_family_model()
            refresh_token_model = get_refresh_token_model()
            auth_token_model = get_token_model()

            member = refresh_family_model.objects.filter(refresh_token=refresh_token[:CONSTANTS.TOKEN_KEY_LENGTH]).first()
            if member is None:
                raise exceptions.AuthenticationFailed(_('Invalid token.'))

            family = refresh_family_model.objects.filter(parent=member.parent)
            newest_member = refresh_family_model.objects.filter(parent=member.parent).order_by('created').last()
            
            
            if  newest_member.refresh_token == refresh_token[:CONSTANTS.TOKEN_KEY_LENGTH]:
                user, token = self.authenticate_refresh_token(refresh_token)
                if user: 
                    self.request.user = user
                    for token in family:
                        auth_token_model.objects.filter(token_key=token.token).delete()
                        refresh_token_model.objects.filter(token_key=token.refresh_token).delete()
                    token_log_limit= settings.MAX_TOKEN_LOG
                    if family.count() >= token_log_limit:
                        ordered_queryset = family.order_by('-created')
                        cutoff_entry = ordered_queryset[token_log_limit-1] 
                        cutoff_entry_timestamp = cutoff_entry.created
                        family.filter(created__lt = cutoff_entry_timestamp).delete() 

                    new_token_instance,new_token = self.create_token() 
                    new_refresh_instance,new_refresh_token= self.create_refresh_token()
                    self.create_refresh_family(parent=member.parent,refresh_token=new_refresh_token,token=new_token) 

                    data = self.get_post_response_data(token=new_token, instance=new_token_instance,refresh_token=new_refresh_token,refresh_token_instance=new_refresh_instance)
                    return Response(data)
                # auth failed
                raise exceptions.AuthenticationFailed(_('Invalid token.'))
            # not newest
            for member in family:
                auth_token_model.objects.filter(token_key=member.token).delete()
                refresh_token_model.objects.filter(token_key=member.refresh_token).delete()
            family.delete() 
            raise exceptions.AuthenticationFailed(_('Invalid token.'))
      
        raise exceptions.AuthenticationFailed(_('Invalid token.'))
    

    def authenticate_refresh_token(self, token):
        '''
        Due to the random nature of hashing a value, this must inspect
        each refresh_token individually to find the correct one.

        Tokens that have expired will be deleted and skipped
        '''
        msg = _('Invalid token.')
        if isinstance(token, bytes):
            token = token.decode("utf-8")
        for refresh_token in get_refresh_token_model().objects.filter(
                token_key=token[:CONSTANTS.TOKEN_KEY_LENGTH]):
            if self._cleanup_token(refresh_token):
                continue
            try:
                digest = hash_token(token)
            except (TypeError, binascii.Error):
                raise exceptions.AuthenticationFailed(msg)
            if compare_digest(digest, refresh_token.digest):
                return self.validate_user(refresh_token)
        raise exceptions.AuthenticationFailed(msg)
    
    def validate_user(self,token):
        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(
                _('User inactive or deleted.'))
        return (token.user, token)

    def _cleanup_token(self, token):
        for other_token in token.user.refresh_token_set.all():
            if other_token.digest != token.digest and other_token.expiry:
                if other_token.expiry < timezone.now():
                    get_refresh_family_model().objects.filter(
                                parent=get_refresh_family_model().objects.filter(
                                refresh_token=other_token.token_key
                                .first().parent
                                )
                            ).delete()
                    other_token.delete()
                    username = other_token.user.get_username()
                    refresh_token_expired.send(sender=self.__class__,
                                       username=username, source="other_token")
        if token.expiry is not None:
            if token.expiry < timezone.now():
                username = token.user.get_username()
                token.delete()
                token_expired.send(sender=self.__class__,
                                   username=username, source="refresh_token")
                return True
        return False



 


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
            token_model = get_token_model()
            parent=refresh_family_model.objects.filter(
                    token=token.token_key).first().parent
            family = refresh_family_model.objects.filter(
                        parent=parent                    
                    )
            
            for token in family:
                auth_token = token_model.objects.filter(token_key=token.token)
                refresh_token =refresh_token_model.objects.filter(token_key=token.refresh_token)
                refresh_token.delete()
                auth_token.delete()
                
            family.delete()
        else:
            token.delete()

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
        if knox_settings.ENABLE_REFRESH_TOKEN:
            request.user.refresh_token_set.all().delete() 
            request.user.refresh_family_set.all().delete()

        user_logged_out.send(sender=request.user.__class__,
                             request=request, user=request.user)
        return self.get_post_response(request)

from django.contrib.auth import get_user_model
from django.db.models.expressions import fields
from rest_framework import serializers

from knox.models import get_refresh_token_model
from knox.settings import CONSTANTS


User = get_user_model()

username_field = User.USERNAME_FIELD if hasattr(User, 'USERNAME_FIELD') else 'username'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (username_field,)


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(max_length=64)   
   

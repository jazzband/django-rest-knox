from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import serializers

from knox.settings import knox_settings


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name',)


def validate_max_time(time):
    if knox_settings.MAX_TOKEN_TTL is not None:
        if time is None or time > knox_settings.MAX_TOKEN_TTL:
            raise serializers.ValidationError("Expiry time is too big")


class ExpirySerializer(serializers.Serializer):
    time = serializers.DurationField(required=False, allow_null=True, validators=[validate_max_time])

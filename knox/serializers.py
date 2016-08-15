from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

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
            raise serializers.ValidationError(_('Expiry time is too big'))


def validate_max_use(use):
    if knox_settings.MAX_TOKEN_USE is not None:
        if use is None or use > knox_settings.MAX_TOKEN_USE:
            raise serializers.ValidationError(_('Expiry use is too big'))


class ExpirySerializer(serializers.Serializer):
    time = serializers.DurationField(required=False, allow_null=True, validators=[validate_max_time])
    use = serializers.IntegerField(required=False, allow_null=True, min_value=0, validators=[validate_max_use])

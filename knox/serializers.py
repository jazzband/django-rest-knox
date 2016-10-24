from django.contrib.auth import get_user_model

from rest_framework import serializers

User = get_user_model()

username_field = User.USERNAME_FIELD if hasattr(User, 'USERNAME_FIELD') else 'username'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (username_field, 'first_name', 'last_name',)

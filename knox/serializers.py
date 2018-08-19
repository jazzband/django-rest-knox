from django.contrib.auth import authenticate, get_user_model

from rest_framework import serializers

User = get_user_model()

username_field = User.USERNAME_FIELD if hasattr(User, 'USERNAME_FIELD') else 'username'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (username_field, 'first_name', 'last_name',)


class TokenSerializer(serializers.Serializer):

    @property
    def username_field(self):
        try:
            username_field = get_user_model().USERNAME_FIELD
        except AttributeError:
            username_field = 'username'
        return username_field

    def __init__(self, *args, **kwargs):
        super(TokenSerializer, self).__init__(*args, **kwargs)
        self.fields[self.username_field] = serializers.CharField()
        self.fields['password'] = serializers.CharField(write_only=True)

    def validate(self, attrs):

        credentials = {
            username_field: attrs.get(self.username_field),
            'password': attrs.get('password')
        }

        if all(credentials.values()):
            user = authenticate(**credentials)
            if user:
                if not user.is_active:
                    msg = 'User account is disabled.'
                    raise serializers.ValidationError(msg)
                return {
                    'user': user
                }
            else:
                msg = 'Unable to login with provided credentials.'
                raise serializers.ValidationError(msg)
        else:
            msg = 'Must include "{username_field}" and "password".'
            msg = msg.format(username_field=self.username_field)
            raise serializers.ValidationError(msg)
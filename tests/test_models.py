from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from knox.models import AuthToken
from knox.settings import CONSTANTS, knox_settings


class AuthTokenTests(TestCase):
    """
    Auth token model tests.
    """

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_token_creation(self):
        """
        Test that tokens are created correctly with expected format.
        """
        token_creation = timezone.now()
        with freeze_time(token_creation):
            instance, token = AuthToken.objects.create(user=self.user)
            self.assertIsNotNone(token)
            self.assertTrue(token.startswith(knox_settings.TOKEN_PREFIX))
            self.assertEqual(
                len(instance.token_key),
                CONSTANTS.TOKEN_KEY_LENGTH,
            )
            self.assertEqual(instance.user, self.user)
            self.assertEqual(
                instance.expiry,
                token_creation + timedelta(hours=10)
            )

    def test_token_creation_with_expiry(self):
        """
        Test token creation with explicit expiry time.
        """
        expiry_time = timedelta(hours=10)
        before_creation = timezone.now()
        instance, _ = AuthToken.objects.create(
            user=self.user,
            expiry=expiry_time
        )
        self.assertIsNotNone(instance.expiry)
        self.assertTrue(before_creation < instance.expiry)
        self.assertTrue(
            (instance.expiry - before_creation - expiry_time).total_seconds() < 1
        )

    def test_token_string_representation(self):
        """
        Test the string representation of AuthToken.
        """
        instance, _ = AuthToken.objects.create(user=self.user)
        expected_str = f'{instance.digest} : {self.user}'
        self.assertEqual(str(instance), expected_str)

    def test_multiple_tokens_for_user(self):
        """
        Test that a user can have multiple valid tokens.
        """
        token1, _ = AuthToken.objects.create(user=self.user)
        token2, _ = AuthToken.objects.create(user=self.user)
        user_tokens = self.user.auth_token_set.all()
        self.assertEqual(user_tokens.count(), 2)
        self.assertNotEqual(token1.digest, token2.digest)

    def test_token_with_custom_prefix(self):
        """
        Test token creation with custom prefix.
        """
        custom_prefix = "TEST_"
        instance, token = AuthToken.objects.create(
            user=self.user,
            prefix=custom_prefix
        )
        self.assertTrue(token.startswith(custom_prefix))
        self.assertTrue(instance.token_key.startswith(custom_prefix))

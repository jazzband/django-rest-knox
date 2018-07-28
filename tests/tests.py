import base64
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings

try:
    # For django >= 2.0
    from django.urls import reverse
except ImportError:
    # For django < 2.0
    from django.conf.urls import reverse

from freezegun import freeze_time

from rest_framework.test import (
    APIRequestFactory,
    APITestCase as TestCase
)

from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.settings import CONSTANTS, knox_settings

User = get_user_model()
root_url = reverse('api-root')


def get_basic_auth_header(username, password):
    return 'Basic %s' % base64.b64encode(
        ('%s:%s' % (username, password)).encode('ascii')).decode()

no_auto_refresh_knox = settings.REST_KNOX.copy()
no_auto_refresh_knox["AUTO_REFRESH"] = False


class AuthTestCase(TestCase):

    def setUp(self):
        self.username, self.email, self.password = 'john.doe', 'john.doe@example.com', 'hunter2'
        self.user = User.objects.create_user(self.username, self.email, self.password)

        self.username2, self.email2, self.password2 = 'jane.doe', 'jane.doe@example.com', 'hunter2'
        self.user2 = User.objects.create_user(self.username2, self.email2, self.password2)

    def test_login_creates_keys(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        url = reverse('knox_login')
        self.client.credentials(
            HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password))

        for _ in range(5):
            self.client.post(url, {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 5)
        self.assertTrue(all(e.token_key for e in AuthToken.objects.all()))

    def test_logout_deletes_keys(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        for _ in range(2):
            token = AuthToken.objects.create(user=self.user)
        self.assertEqual(AuthToken.objects.count(), 2)

        url = reverse('knox_logout')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        self.client.post(url, {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 1, 'other tokens should remain after logout')

    def test_logout_all_deletes_keys(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        for _ in range(10):
            token = AuthToken.objects.create(user=self.user)
        self.assertEqual(AuthToken.objects.count(), 10)

        url = reverse('knox_logoutall')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        self.client.post(url, {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 0)

    def test_logout_all_deletes_only_targets_keys(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        for _ in range(10):
            token = AuthToken.objects.create(user=self.user)
            token2 = AuthToken.objects.create(user=self.user2)
        self.assertEqual(AuthToken.objects.count(), 20)

        url = reverse('knox_logoutall')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        self.client.post(url, {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 10, 'tokens from other users should not be affected by logout all')

    def test_expired_tokens_login_fails(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        token = AuthToken.objects.create(
            user=self.user, expires=timedelta(seconds=0))
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        response = self.client.post(root_url, {}, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, {"detail": "Invalid token."})

    def test_expired_tokens_deleted(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        for _ in range(10):
            # 0 TTL gives an expired token
            token = AuthToken.objects.create(
                user=self.user, expires=timedelta(seconds=0))
        self.assertEqual(AuthToken.objects.count(), 10)

        # Attempting a single logout should delete all tokens

        url = reverse('knox_logout')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        self.client.post(url, {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 0)

    def test_update_token_key(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        token = AuthToken.objects.create(self.user)
        rf = APIRequestFactory()
        request = rf.get('/')
        request.META = {'HTTP_AUTHORIZATION': 'Token {}'.format(token)}
        (self.user, auth_token) = TokenAuthentication().authenticate(request)
        self.assertEqual(
            token[:CONSTANTS.TOKEN_KEY_LENGTH],
            auth_token.token_key)

    def test_invalid_token_length_returns_401_code(self):
        invalid_token = "1" * (CONSTANTS.TOKEN_KEY_LENGTH - 1)
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % invalid_token))
        response = self.client.post(root_url, {}, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, {"detail": "Invalid token."})

    def test_invalid_odd_length_token_returns_401_code(self):
        token = AuthToken.objects.create(self.user)
        odd_length_token = token + '1'
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % odd_length_token))
        response = self.client.post(root_url, {}, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, {"detail": "Invalid token."})

    def test_token_expiry_is_extended_with_auto_refresh_activated(self):
        self.assertEqual(settings.REST_KNOX["AUTO_REFRESH"], True)
        self.assertEqual(knox_settings.TOKEN_TTL, timedelta(hours=10))
        ttl = knox_settings.TOKEN_TTL
        original_time = datetime(2018, 7, 25, 0, 0, 0, 0)

        with freeze_time(original_time):
            token_key = AuthToken.objects.create(user=self.user)

        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token_key))
        five_hours_later = original_time + timedelta(hours=5)
        with freeze_time(five_hours_later):
            response = self.client.get(root_url, {}, format='json')
        self.assertEqual(response.status_code, 200)

        # original expiry date was extended:
        new_expiry = AuthToken.objects.get().expires
        self.assertEqual(new_expiry.replace(tzinfo=None),
                         original_time + ttl + timedelta(hours=5))

        # token works after orignal expiry:
        after_original_expiry = original_time + ttl + timedelta(hours=1)
        with freeze_time(after_original_expiry):
            response = self.client.get(root_url, {}, format='json')
            self.assertEqual(response.status_code, 200)

        # token does not work after new expiry:
        new_expiry = AuthToken.objects.get().expires
        with freeze_time(new_expiry + timedelta(seconds=1)):
            response = self.client.get(root_url, {}, format='json')
            self.assertEqual(response.status_code, 401)

    @override_settings(REST_KNOX=no_auto_refresh_knox)
    def test_token_expiry_is_not_extended_with_auto_refresh_deativated(self):
        self.assertEqual(knox_settings.TOKEN_TTL, timedelta(hours=10))

        now = datetime.now()
        with freeze_time(now):
            token_key = AuthToken.objects.create(user=self.user)

        original_expiry = AuthToken.objects.get().expires

        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token_key))
        with freeze_time(now + timedelta(hours=1)):
            response = self.client.get(root_url, {}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(original_expiry, AuthToken.objects.get().expires)

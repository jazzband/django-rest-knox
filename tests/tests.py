import base64
import datetime

from django.contrib.auth import get_user_model

try:
    # For django >= 2.0
    from django.urls import reverse
except ImportError:
    # For django < 2.0
    from django.conf.urls import reverse

from rest_framework.test import APIRequestFactory, APITestCase as TestCase

from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.settings import CONSTANTS

User = get_user_model()


def get_basic_auth_header(username, password):
    return 'Basic %s' % base64.b64encode(
        ('%s:%s' % (username, password)).encode('ascii')).decode()


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
            user=self.user, expires=datetime.timedelta(seconds=0))
        url = reverse('api-root')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, {"detail": "Invalid token."})

    def test_expired_tokens_deleted(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        for _ in range(10):
            # 0 TTL gives an expired token
            token = AuthToken.objects.create(
                user=self.user, expires=datetime.timedelta(seconds=0))
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
        url = reverse('api-root')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % invalid_token))
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, {"detail": "Invalid token."})

    def test_invalid_odd_length_token_returns_401_code(self):
        user = User.objects.create_user('john.doe', 'root@localhost.com', 'test_pwd')
        token = AuthToken.objects.create(user)
        odd_length_token = token + '1'
        url = reverse('api-root')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % odd_length_token))
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, {"detail": "Invalid token."})

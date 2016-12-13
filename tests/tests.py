import base64
import datetime
import json

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from rest_framework.test import APIRequestFactory, APITestCase as TestCase

from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.settings import CONSTANTS

User = get_user_model()


def get_basic_auth_header(username, password):
    return 'Basic %s' % base64.b64encode(
        ('%s:%s' % (username, password)).encode('ascii')).decode()


class AuthTestCase(TestCase):

    def test_login_creates_keys(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        User.objects.create_user(username, 'root@localhost.com', password)
        url = reverse('knox_login')
        self.client.credentials(
            HTTP_AUTHORIZATION=get_basic_auth_header(username, password))

        for _ in range(5):
            self.client.post(url, {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 5)
        self.assertTrue(all(e.token_key for e in AuthToken.objects.all()))

    def test_logout_deletes_keys(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        user = User.objects.create_user(
            username, 'root@localhost.com', password)
        token = AuthToken.objects.create(user=user)
        self.assertEqual(AuthToken.objects.count(), 1)

        url = reverse('knox_logout')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        self.client.post(url, {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 0)

    def test_logout_all_deletes_keys(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        user = User.objects.create_user(
            username, 'root@localhost.com', password)
        for _ in range(10):
            token = AuthToken.objects.create(user=user)
        self.assertEqual(AuthToken.objects.count(), 10)

        url = reverse('knox_logoutall')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        self.client.post(url, {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 0)

    def test_expired_tokens_deleted(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        user = User.objects.create_user(
            username, 'root@localhost.com', password)
        for _ in range(10):
            # 0 TTL gives an expired token
            token = AuthToken.objects.create(
                user=user, expires=datetime.timedelta(seconds=0))
        self.assertEqual(AuthToken.objects.count(), 10)

        # Attempting a single logout should delete all tokens

        url = reverse('knox_logout')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        self.client.post(url, {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 0)

    def test_update_token_key(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        user = User.objects.create_user(
            username, 'root@localhost.com', password)
        token = AuthToken.objects.create(user)
        auth_token = AuthToken.objects.first()
        auth_token.token_key = None
        auth_token.save()
        rf = APIRequestFactory()
        request = rf.get('/')
        request.META = {'HTTP_AUTHORIZATION': 'Token {}'.format(token)}
        TokenAuthentication().authenticate(request)
        auth_token = AuthToken.objects.get(digest=auth_token.digest)
        self.assertEqual(
            token[:CONSTANTS.TOKEN_KEY_LENGTH],
            auth_token.token_key)

    def test_invalid_token_length_returns_401_code(self):
        invalid_token = "1" * (CONSTANTS.TOKEN_KEY_LENGTH - 1)
        url = reverse('api-root')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % invalid_token))
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response), {"detail": "Invalid token."})

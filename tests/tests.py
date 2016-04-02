import json
import base64
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase as TestCase
from rest_framework.test import force_authenticate
from rest_framework.settings import api_settings

from knox.models import AuthToken
from knox.settings import knox_settings

User = get_user_model()


def get_basic_auth_header(username, password):
    return 'Basic %s' % base64.b64encode(('%s:%s' % (username, password)).encode('ascii')).decode()


def get_token_auth_header(token):
    return 'Token ' + token


def get_older_token():
    return AuthToken.objects.all().order_by('created')[0]


class AuthTestCase(TestCase):

    def test_login_creates_keys(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        User.objects.create_user(username, 'root@localhost.com', password)
        url = reverse('knox_login')
        self.client.credentials(HTTP_AUTHORIZATION=get_basic_auth_header(username, password))

        for _ in range(5):
            self.client.post(url, {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 5)

    def test_logout_deletes_keys(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        user = User.objects.create_user(username, 'root@localhost.com', password)
        token = AuthToken.objects.create(user=user)
        self.assertEqual(AuthToken.objects.count(), 1)

        url = reverse('knox_logout')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        self.client.post(url, {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 0)

    def test_logout_all_deletes_keys(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        user = User.objects.create_user(username, 'root@localhost.com', password)
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
        user = User.objects.create_user(username, 'root@localhost.com', password)
        for _ in range(10):
            token = AuthToken.objects.create(user=user, time=timedelta(seconds=0)) #0 TTL gives an expired token
        self.assertEqual(AuthToken.objects.count(), 10)

        # Attempting a single logout should delete all tokens
        url = reverse('knox_logout')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        self.client.post(url, {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 0)

    def test_login_with_time(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        user = User.objects.create_user(username, 'root@localhost.com', password)
        url = reverse('knox_login')
        self.client.credentials(HTTP_AUTHORIZATION=get_basic_auth_header(username, password))
        self.client.post(url + "?time=10", {}, format='json')
        greater_duration = timedelta(minutes=5)
        self.assertEqual(AuthToken.objects.count(), 1)
        token = AuthToken.objects.get()
        self.assertTrue(token.time < greater_duration)

    def test_login_with_invalid_time_format(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        user = User.objects.create_user(username, 'root@localhost.com', password)
        url = reverse('knox_login')
        self.client.credentials(HTTP_AUTHORIZATION=get_basic_auth_header(username, password))
        res = self.client.post(url + "?time=spam", {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AuthToken.objects.count(), 0)

    def test_login_with_time_too_big(self):
        old_MAX_TOKEN_TTL = knox_settings.MAX_TOKEN_TTL
        knox_settings.MAX_TOKEN_TTL = timedelta(seconds=5)

        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        user = User.objects.create_user(username, 'root@localhost.com', password)
        url = reverse('knox_login')
        self.client.credentials(HTTP_AUTHORIZATION=get_basic_auth_header(username, password))
        res = self.client.post(url + "?time=20", {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AuthToken.objects.count(), 0)

        knox_settings.MAX_TOKEN_TTL = old_MAX_TOKEN_TTL

    def test_login_with_no_max_expiry(self):
        old_MAX_TOKEN_TTL = knox_settings.MAX_TOKEN_TTL
        knox_settings.MAX_TOKEN_TTL = None

        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        user = User.objects.create_user(username, 'root@localhost.com', password)
        url = reverse('knox_login')
        self.client.credentials(HTTP_AUTHORIZATION=get_basic_auth_header(username, password))
        res = self.client.post(url + "?time=10:10:10", {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(AuthToken.objects.count(), 1)

        knox_settings.MAX_TOKEN_TTL = old_MAX_TOKEN_TTL

    def test_login_with_use(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        url = reverse('test_dummy')
        res = self.client.get(url, {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        username, password = 'root', 'toor'
        user = User.objects.create_user(username, 'root@localhost.com', password)
        self.client.credentials(HTTP_AUTHORIZATION=get_basic_auth_header(username, password))
        url = reverse('knox_login')
        res = self.client.post(url + "?use=1", {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(AuthToken.objects.count(), 1)
        self.assertEqual(get_older_token().use, 1)
        self.client.credentials(HTTP_AUTHORIZATION=get_token_auth_header(res.data['token']))
        url = reverse('test_dummy')
        res = self.client.get(url, {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_token_decrement(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        user = User.objects.create_user(username, 'root@localhost.com', password)
        AuthToken.objects.create(user, use=1)
        self.assertEqual(AuthToken.objects.count(), 1)
        auth_token = get_older_token()
        self.assertEqual(auth_token.use, 1)
        auth_token.decrement()
        self.assertEqual(auth_token.use, 0)

    def test_use_decrements_and_deletes_token(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        user = User.objects.create_user(username, 'root@localhost.com', password)
        url = reverse('knox_login')
        self.client.credentials(HTTP_AUTHORIZATION=get_basic_auth_header(username, password))
        use = 7
        res = self.client.post(url + "?use=" + str(use), {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=get_token_auth_header(res.data['token']))
        url = reverse('test_dummy')
        for i in range(use):
            self.assertEqual(get_older_token().use, use - i)
            res = self.client.get(url, {}, format='json')
            self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_older_token().use, 0)
        res = self.client.get(url, {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(AuthToken.objects.count(), 0)

    def test_login_with_invalid_use_format(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        user = User.objects.create_user(username, 'root@localhost.com', password)
        url = reverse('knox_login')
        self.client.credentials(HTTP_AUTHORIZATION=get_basic_auth_header(username, password))
        res = self.client.post(url + "?use=spam", {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AuthToken.objects.count(), 0)

    def test_login_with_use_too_big(self):
        old_MAX_TOKEN_USE = knox_settings.MAX_TOKEN_USE
        knox_settings.MAX_TOKEN_USE = 4

        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        user = User.objects.create_user(username, 'root@localhost.com', password)
        url = reverse('knox_login')
        self.client.credentials(HTTP_AUTHORIZATION=get_basic_auth_header(username, password))
        res = self.client.post(url + "?use=20", {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AuthToken.objects.count(), 0)

        knox_settings.MAX_TOKEN_USE = old_MAX_TOKEN_USE

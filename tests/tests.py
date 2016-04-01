import json
import base64
import datetime

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase as TestCase

from knox.models import AuthToken
from knox.settings import knox_settings

User = get_user_model()

def get_basic_auth_header(username, password):
    return 'Basic %s' % base64.b64encode(('%s:%s' % (username, password)).encode('ascii')).decode()

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
            token = AuthToken.objects.create(user=user, time=datetime.timedelta(seconds=0)) #0 TTL gives an expired token
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
        greater_expiry = timezone.now() + datetime.timedelta(minutes=5)
        url = reverse('knox_login')
        self.client.credentials(HTTP_AUTHORIZATION=get_basic_auth_header(username, password))
        self.client.post(url + "?time=10", {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 1)
        token = AuthToken.objects.get()
        self.assertTrue(token.expires < greater_expiry)

    def test_login_with_invalid_time_format(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        user = User.objects.create_user(username, 'root@localhost.com', password)
        greater_expiry = timezone.now() + datetime.timedelta(hours=60)
        url = reverse('knox_login')
        self.client.credentials(HTTP_AUTHORIZATION=get_basic_auth_header(username, password))
        res = self.client.post(url + "?time=spam", {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AuthToken.objects.count(), 0)

    def test_login_with_time_too_big(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        user = User.objects.create_user(username, 'root@localhost.com', password)
        big_expiry = knox_settings.MAX_TOKEN_TTL + datetime.timedelta(minutes=5)
        url = reverse('knox_login')
        self.client.credentials(HTTP_AUTHORIZATION=get_basic_auth_header(username, password))
        res = self.client.post(url + "?time=" + str(big_expiry.seconds), {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AuthToken.objects.count(), 0)

    def test_login_with_no_max_expiry(self):
        old_MAX_TOKEN_TTL = knox_settings.MAX_TOKEN_TTL
        knox_settings.MAX_TOKEN_TTL = None

        self.assertEqual(AuthToken.objects.count(), 0)
        username, password = 'root', 'toor'
        user = User.objects.create_user(username, 'root@localhost.com', password)
        big_expiry = old_MAX_TOKEN_TTL + datetime.timedelta(minutes=5)
        url = reverse('knox_login')
        self.client.credentials(HTTP_AUTHORIZATION=get_basic_auth_header(username, password))
        res = self.client.post(url + "?time=" + str(big_expiry.seconds), {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(AuthToken.objects.count(), 1)

        knox_settings.MAX_TOKEN_TTL = old_MAX_TOKEN_TTL

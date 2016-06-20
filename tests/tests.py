import json
import base64
import datetime

from cryptography import fernet

from django.utils import encoding
from django.utils import http
from django.db import connection
from django.contrib.auth import get_user_model
from django.contrib.auth import tokens
from django.core.urlresolvers import reverse

from rest_framework import test

from knox.models import AuthToken
from knox import crypto
from knox import knox_rest_auth

User = get_user_model()

def get_basic_auth_header(username, password):
    return 'Basic %s' % base64.b64encode(('%s:%s' % (username, password)).encode('ascii')).decode()


class AuthTestCase(test.APITestCase):

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
            token = AuthToken.objects.create(user=user, expires=datetime.timedelta(seconds=0)) #0 TTL gives an expired token
        self.assertEqual(AuthToken.objects.count(), 10)

        # Attempting a single logout should delete all tokens

        url = reverse('knox_logout')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        self.client.post(url, {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 0)

    def test_encrypted_token(self):
        """
        The token is encrypted with the provided password.
        """
        user = User.objects.create_user(
            username='foo-username', password='foo-secret')
        token = AuthToken.objects.create(user=user, password='foo-secret')
        token_obj = AuthToken.objects.get(user=user)
        self.assertNotEqual(
            token_obj.encrypted, token, 'Token unencrypted on instance')
        self.assertEqual(
            token_obj.decrypt('foo-secret'), token,
            'Wrong decrypted instance token value')
        with connection.cursor() as cur:
            cur.execute("SELECT encrypted FROM {0} where digest='{1}'".format(
                AuthToken._meta.db_table, token_obj.digest))
            data = [encoding.force_text(r[0]) for r in cur.fetchall()]
        self.assertNotEqual(
            data[0], token, 'Token unencrypted in DB')
        foo_codec = fernet.Fernet(crypto.derive_fernet_key(
            'foo-secret', token_obj.salt))
        self.assertEqual(
            foo_codec.decrypt(encoding.force_bytes(data[0])), token,
            'Wrong decrypted DB token value')

        self.client.credentials(HTTP_AUTHORIZATION=get_basic_auth_header(
            user.username, 'foo-secret'))
        with self.settings(OLD_PASSWORD_FIELD_ENABLED=True):
            change_response = self.client.post(
                '/api/auth/password/change/', dict(
                    old_password='foo-secret',
                    new_password1='bar-secret', new_password2='bar-secret'),
                format='json')
            self.assertEqual(change_response.status_code, 200)
        user = User.objects.get(username='foo-username')
        self.client.credentials(HTTP_AUTHORIZATION=get_basic_auth_header(
            user.username, 'bar-secret'))

        token_obj = AuthToken.objects.get(user=user)
        self.assertNotEqual(
            token_obj.encrypted, token, 'Token unencrypted on instance')
        with self.assertRaises(
                fernet.InvalidToken,
                msg='Instance token encrypted with the old password'):
            self.assertNotEqual(
                token_obj.decrypt('foo-secret'), token,
                'Instance token encrypted with the old password')
        self.assertEqual(
            token_obj.decrypt('bar-secret'), token,
            'Instance token not encrypted with the new password')
        with connection.cursor() as cur:
            cur.execute("SELECT encrypted FROM {0} where digest='{1}'".format(
                AuthToken._meta.db_table, token_obj.digest))
            data = [encoding.force_text(r[0]) for r in cur.fetchall()]
        self.assertNotEqual(
            data[0], token, 'Token unencrypted in DB')
        bar_codec = fernet.Fernet(crypto.derive_fernet_key(
            'bar-secret', token_obj.salt))
        with self.assertRaises(
                fernet.InvalidToken,
                msg='DB token encrypted with the old password'):
            self.assertNotEqual(
                foo_codec.decrypt(encoding.force_bytes(data[0])), token,
                'DB token encrypted with the old password')
        self.assertEqual(
            bar_codec.decrypt(encoding.force_bytes(data[0])), token,
            'DB token not encrypted with the new password')

        reset_response = self.client.post(
            '/api/auth/password/reset/confirm/', dict(
                uid=http.urlsafe_base64_encode(str(user.id)),
                token=tokens.default_token_generator.make_token(user),
                new_password1='qux-secret', new_password2='qux-secret'),
            format='json')
        self.assertEqual(reset_response.status_code, 200)

        self.assertFalse(
            AuthToken.objects.exists(),
            'Encrypted tokens were not erased on reset')

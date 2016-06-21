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
            encoding.force_str(
                foo_codec.decrypt(encoding.force_bytes(data[0]))), token,
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
            encoding.force_str(
                bar_codec.decrypt(encoding.force_bytes(data[0]))), token,
            'DB token not encrypted with the new password')

        reset_response = self.client.post(
            '/api/auth/password/reset/confirm/', dict(
                uid=encoding.force_str(http.urlsafe_base64_encode(
                    encoding.force_bytes(user.id))),
                token=tokens.default_token_generator.make_token(user),
                new_password1='qux-secret', new_password2='qux-secret'),
            format='json')
        self.assertEqual(reset_response.status_code, 200)

        self.assertFalse(
            AuthToken.objects.exists(),
            'Encrypted tokens were not erased on reset')

    def test_tokens_endpoint(self):
        """
        The tokens endpoint supports general token management.
        """
        creds = dict(login=dict(
            username='foo-username', password='foo-secret'))
        invalid_creds = dict(login=dict(
            username='foo-username', password='bar-secret'))
        user = User.objects.create_user(**creds['login'])
        self.client.credentials(HTTP_AUTHORIZATION=get_basic_auth_header(
            creds['login']['username'], creds['login']['password']))
        token = AuthToken.objects.create(
            user=user, password=creds['login']['password'])
        tokens = AuthToken.objects.filter(user=user).order_by('created')
        token_obj = tokens.get()
        token_json = dict(
            pk=token_obj.pk, token=token,
            created=token_obj.created.replace(tzinfo=None).isoformat() + 'Z',
            expires=token_obj.expires.replace(tzinfo=None).isoformat() + 'Z')

        # HTTP methods that may ignore entity bodies are not allowed,
        # with or without credentials included
        for method in ('get', 'delete'):
            response = getattr(self.client, method)(
                '/api/auth/tokens/', format='json')
            self.assertEqual(
                response.status_code, 405,
                'GET method should not be supported')
            response = getattr(self.client, method)(
                '/api/auth/tokens/{0}/'.format(token_obj.pk), format='json')
            self.assertEqual(
                response.status_code, 405,
                'GET method should not be supported')
            response = getattr(self.client, method)(
                '/api/auth/tokens/', creds, format='json')
            self.assertEqual(
                response.status_code, 405,
                'GET method should not be supported')
            response = getattr(self.client, method)(
                '/api/auth/tokens/{0}/'.format(token_obj.pk),
                creds, format='json')
            self.assertEqual(
                response.status_code, 405,
                'GET method should not be supported')

        # Only POST is allowed for the endpoints that replace those methods,
        # with or without credentials included
        for method in ('put', 'patch'):
            response = getattr(self.client, method)(
                '/api/auth/tokens/list/', format='json')
            self.assertEqual(
                response.status_code, 405,
                '{0} method should not be supported'.format(method.upper()))
            response = getattr(self.client, method)(
                '/api/auth/tokens/list/', creds, format='json')
            self.assertEqual(
                response.status_code, 405,
                '{0} method should not be supported'.format(method.upper()))
            for detail_action in ('retrieve', 'destroy'):
                response = getattr(self.client, method)(
                    '/api/auth/tokens/{0}/{1}/'.format(
                        token_obj.pk, detail_action), format='json')
                self.assertEqual(
                    response.status_code, 405,
                    '{0} method should not be supported'.format(
                        method.upper()))
                response = getattr(self.client, method)(
                    '/api/auth/tokens/{0}/{1}/'.format(
                        token_obj.pk, detail_action), creds, format='json')
                self.assertEqual(
                    response.status_code, 405,
                    '{0} method should not be supported'.format(
                        method.upper()))

        # Allowed endpoints and methods all require credentials
        response = self.client.post('/api/auth/tokens/', format='json')
        self.assertEqual(
            response.status_code, 400,
            'Wrong response to missing credentials')
        response = self.client.post(
            '/api/auth/tokens/', invalid_creds, format='json')
        self.assertEqual(
            response.status_code, 400,
            'Wrong response to invalid credentials')
        for method in ('put', 'patch'):
            response = getattr(self.client, method)(
                '/api/auth/tokens/{0}/'.format(token_obj.pk),
                format='json')
            self.assertEqual(
                response.status_code, 400,
                'Wrong response to missing credentials')
            response = getattr(self.client, method)(
                '/api/auth/tokens/{0}/'.format(token_obj.pk),
                invalid_creds, format='json')
            self.assertEqual(
                response.status_code, 400,
                'Wrong response to invalid credentials')
        response = self.client.post(
            '/api/auth/tokens/list/', format='json')
        self.assertEqual(
            response.status_code, 400,
            'Wrong response to missing credentials')
        response = self.client.post(
            '/api/auth/tokens/list/', invalid_creds, format='json')
        self.assertEqual(
            response.status_code, 400,
            'Wrong response to invalid credentials')
        for detail_action in ('retrieve', 'destroy'):
            response = self.client.post(
                '/api/auth/tokens/{0}/{1}/'.format(
                    token_obj.pk, detail_action),
                format='json')
            self.assertEqual(
                response.status_code, 400,
                'Wrong response to missing credentials')
            response = self.client.post(
                '/api/auth/tokens/{0}/{1}/'.format(
                    token_obj.pk, detail_action),
                invalid_creds, format='json')
            self.assertEqual(
                response.status_code, 400,
                'Wrong response to invalid credentials')

        list_response = self.client.post(
            '/api/auth/tokens/list/', creds, format='json')
        self.assertEqual(
            list_response.status_code, 200, 'List request did not succeed')
        self.assertIsInstance(
            list_response.data, list, 'Wrong type returned')
        self.assertEqual(
            len(list_response.data), 1, 'Wrong number of results')
        self.assertEqual(
            list_response.data[0], token_json, 'Wrong token JSON')

        retrieve_response = self.client.post(
            '/api/auth/tokens/{0}/retrieve/'.format(token_obj.pk),
            creds, format='json')
        self.assertEqual(
            retrieve_response.status_code, 200,
            'Retrieve request did not succeed')
        self.assertIsInstance(
            retrieve_response.data, dict, 'Wrong type returned')
        self.assertEqual(
            retrieve_response.data, token_json, 'Wrong token JSON')

        create_response = self.client.post(
            '/api/auth/tokens/', creds, format='json')
        self.assertEqual(
            create_response.status_code, 201,
            'Create request did not succeed')
        self.assertIsInstance(
            create_response.data, dict, 'Wrong type returned')
        self.assertEqual(tokens.count(), 2, 'Wrong number of tokens')
        self.assertEqual(
            create_response.data, dict(
                pk=tokens[1].pk,
                token=tokens[1].decrypt(creds['login']['password']),
                created=tokens[1].created.replace(
                    tzinfo=None).isoformat() + 'Z',
                expires=tokens[1].expires.replace(
                    tzinfo=None).isoformat() + 'Z'),
            'Wrong created token JSON')

        destroy_response = self.client.post(
            '/api/auth/tokens/{0}/destroy/'.format(tokens[1].pk),
            creds, format='json')
        self.assertEqual(
            destroy_response.status_code, 204,
            'Destroy request did not succeed')
        self.assertEqual(tokens.count(), 1, 'Wrong number of tokens')

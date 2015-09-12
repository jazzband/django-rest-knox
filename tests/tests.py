import json
import base64

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase as TestCase

from knox.models import AuthToken

User = get_user_model()

def get_basic_auth_header(username, password):
    return 'Basic %s' % base64.b64encode(('%s:%s' % (username, password)).encode('ascii')).decode()

class AuthTestCase(TestCase):

    def test_login_creates_keys(self):
        username, password = 'root', 'toor'
        User.objects.create_user(username, 'root@localhost.com', password)
        url = reverse('knox_login')
        data = {}
        self.client.credentials(HTTP_AUTHORIZATION=get_basic_auth_header(username, password))

        for _ in range(5):
            self.client.post(url, data, format='json')

        self.assertEqual(AuthToken.objects.count(), 5)

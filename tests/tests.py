import json

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase as TestCase

from knox.models import AuthToken

User = get_user_model()

class AuthTestCase(TestCase):

    def test_login_creates_keys(self):
        User.objects.create_user('root', 'root@localhost.com', 'toor')
        

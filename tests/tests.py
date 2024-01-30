import base64
from datetime import datetime, timedelta
from importlib import reload

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from freezegun import freeze_time
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.serializers import DateTimeField
from rest_framework.test import APIRequestFactory, APITestCase as TestCase

from knox import auth, crypto, views
from knox.auth import TokenAuthentication
from knox.models import AuthRefreshToken, AuthToken, RefreshFamily
from knox.serializers import UserSerializer
from knox.settings import CONSTANTS, knox_settings
from knox.signals import token_expired,refresh_token_expired

User = get_user_model()
root_url = reverse('api-root')


def get_basic_auth_header(username, password):
    return 'Basic %s' % base64.b64encode(
        ('%s:%s' % (username, password)).encode('ascii')).decode()


""" 
instead of setting it to true on every test that concerns 
refresh tokens we can just use the global toggle 
and set it to True by default
"""
knox_settings.defaults["ENABLE_REFRESH_TOKEN"] = True
knox_settings.defaults["REFRESH_TOKEN_TTL"] = timedelta(days=7)

refresh_token_limit_per_user = knox_settings.defaults.copy()
refresh_token_limit_per_user["REFRESH_TOKEN_LIMIT_PER_USER"]=10

refresh_token_30_ttl = knox_settings.defaults.copy()
refresh_token_30_ttl["REFRESH_TOKEN_TTL"] = timedelta(days=30)

auto_refresh_knox = knox_settings.defaults.copy()
auto_refresh_knox["AUTO_REFRESH"] = True

token_user_limit_knox = knox_settings.defaults.copy()
token_user_limit_knox["TOKEN_LIMIT_PER_USER"] = 10

refresh_token_history = knox_settings.defaults.copy()
refresh_token_history["MAX_TOKEN_HISTORY"] = 20

refresh_token_history_zero = knox_settings.defaults.copy()
refresh_token_history_zero["MAX_TOKEN_HISTORY"] = 0

refresh_token_history_zero = knox_settings.defaults.copy()
refresh_token_history_zero["MAX_TOKEN_HISTORY"] = 1

token_user_limit_one=knox_settings.defaults.copy()
token_user_limit_one["TOKEN_LIMIT_PER_USER"] = 1

user_serializer_knox = knox_settings.defaults.copy()
user_serializer_knox["USER_SERIALIZER"] = UserSerializer

auth_header_prefix_knox = knox_settings.defaults.copy()
auth_header_prefix_knox["AUTH_HEADER_PREFIX"] = 'Baerer'

token_no_expiration_knox = knox_settings.defaults.copy()
token_no_expiration_knox["REFRESH_TOKEN_TTL"] = None
token_no_expiration_knox["TOKEN_TTL"] = None

EXPIRY_DATETIME_FORMAT = '%H:%M %d/%m/%y'
expiry_datetime_format_knox = knox_settings.defaults.copy()
expiry_datetime_format_knox["EXPIRY_DATETIME_FORMAT"] = EXPIRY_DATETIME_FORMAT

token_prefix = "TEST_"
token_prefix_knox = knox_settings.defaults.copy()
token_prefix_knox["TOKEN_PREFIX"] = token_prefix

token_prefix_too_long = "a" * CONSTANTS.MAXIMUM_TOKEN_PREFIX_LENGTH + "a"
token_prefix_too_long_knox = knox_settings.defaults.copy()
token_prefix_too_long_knox["TOKEN_PREFIX"] = token_prefix_too_long


class AuthTestCase(TestCase):

    def setUp(self):
        self.username = 'john.doe'
        self.email = 'john.doe@example.com'
        self.password = 'hunter2'
        self.user = User.objects.create_user(self.username, self.email, self.password)

        self.username2 = 'jane.doe'
        self.email2 = 'jane.doe@example.com'
        self.password2 = 'hunter2'
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
        

        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.assertEqual(AuthRefreshToken.objects.count(), 5)
            self.assertTrue(all(e.token_key for e in AuthRefreshToken.objects.all()))
            
            self.assertEqual(RefreshFamily.objects.count(), 5)

    def test_login_returns_serialized_token(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        url = reverse('knox_login')
        self.client.credentials(
            HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password)
        )
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(knox_settings.USER_SERIALIZER, None)
        self.assertIn('token', response.data)

        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.assertIn('refresh_token', response.data)
        username_field = self.user.USERNAME_FIELD
        self.assertNotIn(username_field, response.data)

    def test_login_returns_serialized_token_and_username_field(self):

        with override_settings(REST_KNOX=user_serializer_knox):
            reload(views)
            self.assertEqual(AuthToken.objects.count(), 0)
            url = reverse('knox_login')
            self.client.credentials(
                HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password)
            )
            response = self.client.post(url, {}, format='json')
            self.assertEqual(user_serializer_knox["USER_SERIALIZER"], UserSerializer)
        reload(views)
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)
        
        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.assertIn('refresh_token', response.data)
        username_field = self.user.USERNAME_FIELD
        self.assertIn('user', response.data)
        self.assertIn(username_field, response.data['user'])

    def test_login_returns_configured_expiry_datetime_format(self):

        with override_settings(REST_KNOX=expiry_datetime_format_knox):
            reload(views)
            self.assertEqual(AuthToken.objects.count(), 0)
            url = reverse('knox_login')
            self.client.credentials(
                HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password)
            )
            response = self.client.post(url, {}, format='json')
            self.assertEqual(
                expiry_datetime_format_knox["EXPIRY_DATETIME_FORMAT"],
                EXPIRY_DATETIME_FORMAT
            )
        reload(views)
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)

        self.assertNotIn('user', response.data)
        self.assertEqual(
            response.data['expiry'],
            DateTimeField(format=EXPIRY_DATETIME_FORMAT).to_representation(
                AuthToken.objects.first().expiry
            )
        )

        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.assertEqual(
            response.data['refresh_token_expiry'],
            DateTimeField(format=EXPIRY_DATETIME_FORMAT).to_representation(
                AuthRefreshToken.objects.first().expiry
            )
        )

    def test_logout_deletes_keys(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        for _ in range(2):
            instance, token = AuthToken.objects.create(user=self.user)
            
            if knox_settings.ENABLE_REFRESH_TOKEN:
                refresh_instance, refresh_token=AuthRefreshToken.objects.create(user=self.user)
                RefreshFamily.objects.create(user=self.user,parent=refresh_token,refresh_token=refresh_token,token=token)
        
        self.assertEqual(AuthToken.objects.count(), 2)


        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.assertEqual(AuthRefreshToken.objects.count(), 2)
            self.assertEqual(RefreshFamily.objects.count(), 2)
        
        url = reverse('knox_logout')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        self.client.post(url, {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 1,
                         'other tokens should remain after logout')

        
        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.assertEqual(RefreshFamily.objects.count(), 1,
                     
                             'other tokens should remain after logout')


            self.assertEqual(AuthRefreshToken.objects.count(), 1,
                         'other tokens should remain after logout')
        
    def test_logout_all_deletes_keys(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        for _ in range(10):
            instance, token = AuthToken.objects.create(user=self.user)

            if knox_settings.ENABLE_REFRESH_TOKEN:
                refresh_instance, refresh_token=AuthRefreshToken.objects.create(user=self.user)
                RefreshFamily.objects.create(user=self.user,parent=refresh_token,refresh_token=refresh_token,token=token)

        self.assertEqual(AuthToken.objects.count(), 10)

        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.assertEqual(AuthRefreshToken.objects.count(), 10)
            self.assertEqual(RefreshFamily.objects.count(), 10)

        url = reverse('knox_logoutall')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        self.client.post(url, {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 0)

        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.assertEqual(AuthRefreshToken.objects.count(), 0)
            self.assertEqual(RefreshFamily.objects.count(), 0)

    def test_logout_all_deletes_only_targets_keys(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        for _ in range(10):
            instance, token = AuthToken.objects.create(user=self.user)

            if knox_settings.ENABLE_REFRESH_TOKEN:
                refresh_instance, refresh_token=AuthRefreshToken.objects.create(user=self.user)
                RefreshFamily.objects.create(user=self.user,parent=refresh_token,refresh_token=refresh_token,token=token)


            instance, token = AuthToken.objects.create(user=self.user2)
            
            if knox_settings.ENABLE_REFRESH_TOKEN:
                refresh_instance, refresh_token=AuthRefreshToken.objects.create(user=self.user2)
                RefreshFamily.objects.create(user=self.user2,parent=refresh_token,refresh_token=refresh_token,token=token)


        self.assertEqual(AuthToken.objects.count(), 20)

        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.assertEqual(AuthRefreshToken.objects.count(), 20)
            self.assertEqual(RefreshFamily.objects.count(), 20)

        url = reverse('knox_logoutall')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        self.client.post(url, {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 10,
                         'tokens from other users should not be affected by logout all')
        

        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.assertEqual(AuthRefreshToken.objects.count(), 10,
                         'tokens from other users should not be affected by logout all')
            self.assertEqual(RefreshFamily.objects.count(), 10,
                         'tokens from other users should not be affected by logout all')



    def test_expired_tokens_login_fails(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        instance, token = AuthToken.objects.create(
            user=self.user, expiry=timedelta(seconds=-1))

        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        response = self.client.post(root_url, {}, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, {"detail": "Invalid token."})

    def test_expired_tokens_deleted(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        for _ in range(10):
            # -1 TTL gives an expired token
            instance, token = AuthToken.objects.create(
                user=self.user, expiry=timedelta(seconds=-1))

            if knox_settings.ENABLE_REFRESH_TOKEN:
                refresh_instance,refresh_token = AuthRefreshToken.objects.create(
                    user=self.user,expiry=timedelta(seconds=-1))
                RefreshFamily.objects.create(user=self.user,parent=refresh_token,refresh_token=refresh_token,token=token)
            
        self.assertEqual(AuthToken.objects.count(), 10)

        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.assertEqual(AuthRefreshToken.objects.count(), 10)
            self.assertEqual(RefreshFamily.objects.count(), 10)

        # Attempting a single logout should delete all tokens
        url = reverse('knox_logout')
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        self.client.post(url, {}, format='json')
        self.assertEqual(AuthToken.objects.count(), 0)

        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.assertEqual(AuthRefreshToken.objects.count(), 0)
            self.assertEqual(RefreshFamily.objects.count(), 0)


    def test_update_token_key(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        instance, token = AuthToken.objects.create(self.user)
        rf = APIRequestFactory()
        request = rf.get('/')
        request.META = {'HTTP_AUTHORIZATION': 'Token {}'.format(token)}
        (self.user, auth_token) = TokenAuthentication().authenticate(request)
        self.assertEqual(
            token[:CONSTANTS.TOKEN_KEY_LENGTH],
            auth_token.token_key,
        )

    def test_authorization_header_empty(self):
        rf = APIRequestFactory()
        request = rf.get('/')
        request.META = {'HTTP_AUTHORIZATION': ''}
        self.assertEqual(TokenAuthentication().authenticate(request), None)

    def test_authorization_header_prefix_only(self):
        rf = APIRequestFactory()
        request = rf.get('/')
        request.META = {'HTTP_AUTHORIZATION': 'Token'}
        with self.assertRaises(AuthenticationFailed) as err:
            (self.user, auth_token) = TokenAuthentication().authenticate(request)
        self.assertIn(
            'Invalid token header. No credentials provided.',
            str(err.exception),
        )

    def test_authorization_header_spaces_in_token_string(self):
        rf = APIRequestFactory()
        request = rf.get('/')
        request.META = {'HTTP_AUTHORIZATION': 'Token wordone wordtwo'}
        with self.assertRaises(AuthenticationFailed) as err:
            (self.user, auth_token) = TokenAuthentication().authenticate(request)
        self.assertIn(
            'Invalid token header. Token string should not contain spaces.',
            str(err.exception),
        )

    def test_invalid_token_length_returns_401_code(self):
        invalid_token = "1" * (CONSTANTS.TOKEN_KEY_LENGTH - 1)
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % invalid_token))
        response = self.client.post(root_url, {}, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, {"detail": "Invalid token."})

    def test_invalid_odd_length_token_returns_401_code(self):
        instance, token = AuthToken.objects.create(self.user)
        odd_length_token = token + '1'
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % odd_length_token))
        response = self.client.post(root_url, {}, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, {"detail": "Invalid token."})

    def test_token_expiry_is_extended_with_auto_refresh_activated(self):
        ttl = knox_settings.TOKEN_TTL
        original_time = datetime(2018, 7, 25, 0, 0, 0, 0)

        with freeze_time(original_time):
            instance, token = AuthToken.objects.create(user=self.user)

        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        five_hours_later = original_time + timedelta(hours=5)
        with override_settings(REST_KNOX=auto_refresh_knox):
            reload(auth)  # necessary to reload settings in core code
            with freeze_time(five_hours_later):
                response = self.client.get(root_url, {}, format='json')
        reload(auth)
        self.assertEqual(response.status_code, 200)

        # original expiry date was extended:
        new_expiry = AuthToken.objects.get().expiry
        expected_expiry = original_time + ttl + timedelta(hours=5)
        self.assertEqual(new_expiry.replace(tzinfo=None), expected_expiry,
                         "Expiry time should have been extended to {} but is {}."
                         .format(expected_expiry, new_expiry))

        # token works after original expiry:
        after_original_expiry = original_time + ttl + timedelta(hours=1)
        with freeze_time(after_original_expiry):
            response = self.client.get(root_url, {}, format='json')
            self.assertEqual(response.status_code, 200)

        # token does not work after new expiry:
        new_expiry = AuthToken.objects.get().expiry
        with freeze_time(new_expiry + timedelta(seconds=1)):
            response = self.client.get(root_url, {}, format='json')
            self.assertEqual(response.status_code, 401)

    def test_token_expiry_is_not_extended_with_auto_refresh_deactivated(self):
        self.assertEqual(knox_settings.AUTO_REFRESH, False)
        self.assertEqual(knox_settings.TOKEN_TTL, timedelta(hours=10))

        now = datetime.now()
        with freeze_time(now):
            instance, token = AuthToken.objects.create(user=self.user)

        original_expiry = AuthToken.objects.get().expiry

        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        with freeze_time(now + timedelta(hours=1)):
            response = self.client.get(root_url, {}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(original_expiry, AuthToken.objects.get().expiry)

    def test_token_expiry_is_not_extended_within_MIN_REFRESH_INTERVAL(self):
        now = datetime.now()
        with freeze_time(now):
            instance, token = AuthToken.objects.create(user=self.user)

        original_expiry = AuthToken.objects.get().expiry

        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        in_min_interval = now + timedelta(seconds=knox_settings.MIN_REFRESH_INTERVAL - 10)
        with override_settings(REST_KNOX=auto_refresh_knox):
            reload(auth)  # necessary to reload settings in core code
            with freeze_time(in_min_interval):
                response = self.client.get(root_url, {}, format='json')
        reload(auth)  # necessary to reload settings in core code

        self.assertEqual(response.status_code, 200)
        self.assertEqual(original_expiry, AuthToken.objects.get().expiry)

    def test_expiry_signals(self):
        self.signal_was_called = False

        def handler(sender, username, **kwargs):
            self.signal_was_called = True

        token_expired.connect(handler)

        instance, token = AuthToken.objects.create(
            user=self.user,
            expiry=timedelta(seconds=-1),
        )
        self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
        self.client.post(root_url, {}, format='json')
        self.assertTrue(self.signal_was_called)

        
    def test_exceed_token_amount_per_user(self):
        with override_settings(REST_KNOX=token_user_limit_knox):
            reload(views)
            for _ in range(10):
                AuthToken.objects.create(user=self.user)
            url = reverse('knox_login')
            self.client.credentials(
                HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password)
            )
            response = self.client.post(url, {}, format='json')
        reload(views)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data,
                         {"error": "Maximum amount of tokens allowed per user exceeded."})
        
    def test_exceed_refresh_token_amount_per_user(self):
        if knox_settings.ENABLE_REFRESH_TOKEN:
            with override_settings(REST_KNOX=token_user_limit_knox):
                reload(views)
                for _ in range(10):
                        AuthRefreshToken.objects.create(user=self.user)
                self.assertEqual(self.user.refresh_token_set.count(),10)
                url = reverse('knox_login')
                self.client.credentials(
                    HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password)
                )
                response = self.client.post(url, {}, format='json')
            reload(views)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.data,
                         {"error": "Maximum amount of tokens allowed per user exceeded."})
           
     
    def test_does_not_exceed_on_expired_keys(self):

        with override_settings(REST_KNOX=token_user_limit_knox):
            reload(views)
            for _ in range(9):
                AuthToken.objects.create(user=self.user)
            AuthToken.objects.create(user=self.user, expiry=timedelta(seconds=-1))
            # now 10 keys, but only 9 valid so request should succeed.
            url = reverse('knox_login')
            self.client.credentials(
                HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password)
            )
            response = self.client.post(url, {}, format='json')
            failed_response = self.client.post(url, {}, format='json')
        reload(views)
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)
        self.assertEqual(failed_response.status_code, 403)
        self.assertEqual(failed_response.data,
                         {"error": "Maximum amount of tokens allowed per user exceeded."})

    def test_invalid_prefix_return_401(self):

        with override_settings(REST_KNOX=auth_header_prefix_knox):
            reload(auth)
            instance, token = AuthToken.objects.create(user=self.user)
            self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
            failed_response = self.client.get(root_url)
            self.client.credentials(
                HTTP_AUTHORIZATION=(
                    'Baerer %s' % token
                )
            )
            response = self.client.get(root_url)
        reload(auth)
        self.assertEqual(failed_response.status_code, 401)
        self.assertEqual(response.status_code, 200)

    def test_expiry_present_also_when_none(self):
        with override_settings(REST_KNOX=token_no_expiration_knox):
            reload(views)
            self.assertEqual(AuthToken.objects.count(), 0)
            url = reverse('knox_login')
            self.client.credentials(
                HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password)
            )
            response = self.client.post(
                url,
                {},
                format='json'
            )
            self.assertEqual(token_no_expiration_knox["TOKEN_TTL"], None)
            self.assertEqual(response.status_code, 200)
            self.assertIn('token', response.data)
            self.assertIn('expiry', response.data)
            self.assertEqual(
                response.data['expiry'],
                None
            )
            if knox_settings.ENABLE_REFRESH_TOKEN:
                self.assertIn('refresh_token', response.data)
                self.assertIn('refresh_token_expiry', response.data)
                self.assertEqual(
                response.data['refresh_token_expiry'],
                None
            )
            
        reload(views)

    def test_expiry_is_present(self):
        self.assertEqual(AuthToken.objects.count(), 0)
        self.assertEqual(AuthRefreshToken.objects.count(), 0)
        self.assertEqual(RefreshFamily.objects.count(), 0)

        url = reverse('knox_login')
        self.client.credentials(
            HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password)
        )
        response = self.client.post(
            url,
            {},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)
        self.assertIn('expiry', response.data)
        
        self.assertEqual(
            response.data['expiry'],
            DateTimeField().to_representation(AuthToken.objects.first().expiry)
        )

        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.assertIn('refresh_token', response.data)
            self.assertIn('refresh_token_expiry', response.data)
            self.assertEqual(
            response.data['refresh_token_expiry'],
            DateTimeField().to_representation(AuthRefreshToken.objects.first().expiry)
        )


    def test_login_returns_serialized_token_with_prefix_when_prefix_set(self):
        with override_settings(REST_KNOX=token_prefix_knox):
            reload(views)
            reload(crypto)
            self.assertEqual(AuthToken.objects.count(), 0)
            url = reverse('knox_login')
            self.client.credentials(
                HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password)
            )
            response = self.client.post(
                url,
                {},
                format='json'
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.data['token'].startswith(token_prefix))
        reload(views)
        reload(crypto)

    def test_token_with_prefix_returns_200(self):
        with override_settings(REST_KNOX=token_prefix_knox):
            reload(views)
            self.assertEqual(AuthToken.objects.count(), 0)
            url = reverse('knox_login')
            self.client.credentials(
                HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password)
            )
            response = self.client.post(
                url,
                {},
                format='json'
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.data['token'].startswith(token_prefix))
            self.client.credentials(
                HTTP_AUTHORIZATION=('Token %s' % response.data['token'])
            )
            response = self.client.get(root_url, {}, format='json')
            self.assertEqual(response.status_code, 200)
        reload(views)

    def test_prefix_set_longer_than_max_length_raises_valueerror(self):
        with self.assertRaises(ValueError):
            with override_settings(REST_KNOX=token_prefix_too_long_knox):
                pass

    def test_tokens_created_before_prefix_still_work(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password)
        )
        url = reverse('knox_login')
        response = self.client.post(
            url,
            {},
            format='json'
        )
        self.assertFalse(response.data['token'].startswith(token_prefix))
        with override_settings(REST_KNOX=token_prefix_knox):
            reload(views)
            self.client.credentials(
                HTTP_AUTHORIZATION=('Token %s' % response.data['token'])
            )
            response = self.client.get(root_url, {}, format='json')
            self.assertEqual(response.status_code, 200)
        reload(views)

    def test_logout_invalidates_refresh_tokens(self):
        if knox_settings.ENABLE_REFRESH_TOKEN:
            instance, token = AuthToken.objects.create(user=self.user)
            refresh_instance, refresh_token = AuthRefreshToken.objects.create(user=self.user)
            RefreshFamily.objects.create(user=self.user, parent=refresh_token, refresh_token=refresh_token, token=token)
            self.assertEqual(AuthRefreshToken.objects.count(), 1)
            self.assertEqual(RefreshFamily.objects.count(), 1)
            url = reverse('knox_logout')
            self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
            self.client.post(url, {}, format='json')
            self.assertEqual(AuthRefreshToken.objects.count(), 0)
            self.assertEqual(RefreshFamily.objects.count(), 0)
    
    def test_expired_refresh_token_fails(self):
        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.assertEqual(AuthRefreshToken.objects.count(), 0)
            refresh_instance, refresh_token = AuthToken.objects.create(user=self.user, expiry=timedelta(seconds=-1))
            url = reverse('knox_refresh')
            response = self.client.post(url, {'refresh_token': refresh_token}, format='json')
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.data, {"detail": "Invalid token."})
    
    def test_logout_all_invalidates_refresh_tokens(self):
        if knox_settings.ENABLE_REFRESH_TOKEN:
            instance, token = AuthToken.objects.create(user=self.user)
            refresh_instance, refresh_token = AuthRefreshToken.objects.create(user=self.user)
            RefreshFamily.objects.create(user=self.user, parent=refresh_token, refresh_token=refresh_token, token=token)
            self.assertEqual(AuthRefreshToken.objects.count(), 1)
            self.assertEqual(RefreshFamily.objects.count(), 1)
            url = reverse('knox_logoutall')
            self.client.credentials(HTTP_AUTHORIZATION=('Token %s' % token))
            self.client.post(url, {}, format='json')
            self.assertEqual(AuthRefreshToken.objects.count(), 0)
            self.assertEqual(RefreshFamily.objects.count(), 0)
        

    def test_login_returns_refresh_token(self):
        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.client.credentials(
                HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password)
            )
            url = reverse('knox_login')
            response = self.client.post(
                url,
                {},
                format='json'
            )
            self.assertTrue(response.data['refresh_token'])
            self.assertTrue(response.data['token'])
            self.assertTrue(response.data['refresh_token_expiry'])
            
       
    def test_refresh_token_view_returns_new_tokens(self):

        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.client.credentials(
                HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password)
            )
            url = reverse('knox_login')
            response = self.client.post(
                url,
                {},
                format='json'
            )
            self.assertTrue(response.data['refresh_token'])
            self.assertTrue(response.data['token'])
            self.assertTrue(response.data['refresh_token_expiry'])
            refresh_token = response.data['refresh_token']
            token = response.data['token']

 
            url = reverse('knox_refresh')

            self.client.logout()

            response = self.client.post(url,
                {"refresh_token":refresh_token},
                format='json'
            )

            self.assertTrue(response.data['refresh_token'])
            self.assertTrue(response.data['token'])
            self.assertTrue(response.data['refresh_token_expiry'])
       


    def test_refresh_token_invalidate_on_old_token(self):
        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.client.credentials(
                HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password)
            )
            url = reverse('knox_login')
            response = self.client.post(
                url,
                {},
                format='json'
            )
            refresh_token = response.data['refresh_token']
            token = response.data['token']
 
            url = reverse('knox_refresh')

            response = self.client.post(url,
                {"refresh_token":refresh_token},
                format='json'
            )

            response = self.client.post(url,
                {"refresh_token":refresh_token},
                format='json'
            )
            
            self.assertTrue(response.status_code,401)
    
    def test_token_invalidate_on_old_token(self):
        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.client.credentials(
                HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password)
            )
            url = reverse('knox_login')
            response = self.client.post(
                url,
                {},
                format='json'
            )
            
            refresh_token = response.data['refresh_token']
            token = response.data['token']
 
            url = reverse('knox_refresh')
            
            # valid
            response = self.client.post(url,
                {"refresh_token":refresh_token},
                format='json'
            )
            
            #invalid / logout
            response = self.client.post(url,
                {"refresh_token":refresh_token},
                format='json'
            )
            
            #test invalid
            self.client.credentials(
                    HTTP_AUTHORIZATION=("Token "+token)
                    )
            url = reverse('knox_logout')
            response = self.client.post(url,{},format='json')

            self.assertTrue(response.status_code,401)

    def test_using_old_token_only_affects_that_token_family(self):

        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.assertEqual(AuthRefreshToken.objects.count(), 0)
            url = reverse('knox_login')
            self.client.credentials(
                HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password))
            tokens=[]
            for _ in range(2):
                response = self.client.post(url, {}, format='json')
                self.assertTrue(response.data['token'])
                self.assertTrue(response.data['refresh_token'])
                token = response.data['token']
                refresh_token = response.data['refresh_token']

            self.assertTrue(AuthRefreshToken.objects.count(),2)
            

            url = reverse('knox_refresh')
            response = self.client.post(url, {'refresh_token':refresh_token}, format='json')

            self.assertTrue(response.data['token'])
            self.assertTrue(response.data['refresh_token'])

            url = reverse('knox_refresh')
            response = self.client.post(url, {'refresh_token':refresh_token}, format='json')

            self.assertEqual(response.status_code, 401)

            self.assertTrue(AuthRefreshToken.objects.count(),1)


    def test_invalid_refresh_short_token_returns_400(self):
        if knox_settings.ENABLE_REFRESH_TOKEN:
            instance, refresh_token = AuthRefreshToken.objects.create(user=self.user)
            url = reverse('knox_refresh')
            
            # valid
            response = self.client.post(url,
                {"refresh_token":refresh_token[8]},
                format='json'
            )
            
            
            self.assertTrue(response.status_code,400)
    
    def test_invalid_refresh_longer_token_returns_400(self):
        if knox_settings.ENABLE_REFRESH_TOKEN:
            instance, refresh_token = AuthRefreshToken.objects.create(user=self.user)
            url = reverse('knox_refresh')
            
            # valid
            response = self.client.post(url,
                {"refresh_token":refresh_token+"x"},
                format='json'
            )
            
            self.assertTrue(response.status_code,400)

    def test_refresh_history(self):
        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.assertEqual(RefreshFamily.objects.count(), 0)
            url = reverse('knox_login')

            self.client.credentials(
                HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password))
            first = None

            response = self.client.post(url,{},format="json")
            first = response.data["refresh_token"]
            refresh_token = None
            for i in range(10):
                if i == 0:
                    url = reverse("knox_refresh")
                    response = self.client.post(url,{"refresh_token":first},format="json")
                    refresh_token = response.data["refresh_token"]
                else:
                    response = self.client.post(url,{"refresh_token":refresh_token},format="json")
                    refresh_token = response.data["refresh_token"]
                    
            url = reverse("knox_refresh")
            response = self.client.post(url,{"refresh_token":first},format="json")
            
            self.assertEqual(RefreshFamily.objects.count(), 10)

    def test_refresh_history_zero(self):
        if knox_settings.ENABLE_REFRESH_TOKEN:
            with override_settings(REST_KNOX=refresh_token_history_zero):
                reload(views)
                self.assertEqual(RefreshFamily.objects.count(), 0)
                url = reverse('knox_login')

                self.client.credentials(
                    HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password))
                response = self.client.post(url,{},format="json")
                first = response.data["refresh_token"]
                refresh_token = None
                for i in range(2):
                    if i == 0:
                        url = reverse("knox_refresh")
                        response = self.client.post(url,{"refresh_token":first},format="json")
                        refresh_token = response.data["refresh_token"]
                    else:
                        response = self.client.post(url,{"refresh_token":refresh_token},format="json")
                        refresh_token = response.data["refresh_token"]
                        
                url = reverse("knox_refresh")
                response = self.client.post(url,{"refresh_token":first},format="json")
                self.assertTrue(response.status_code != 200) 
                self.assertEqual(RefreshFamily.objects.count(), 1)
            reload(views)


    def test_refresh_history_cleanup(self):
        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.assertEqual(RefreshFamily.objects.count(), 0)
            url = reverse('knox_login')

            self.client.credentials(
                HTTP_AUTHORIZATION=get_basic_auth_header(self.username, self.password))
            first = None

            response = self.client.post(url,{},format="json")
            first = response.data["refresh_token"]
            refresh_token = None
            for i in range(9):
                if i == 0:
                    url = reverse("knox_refresh")
                    response = self.client.post(url,{"refresh_token":first},format="json")
                    refresh_token = response.data["refresh_token"]
                else:
                    response = self.client.post(url,{"refresh_token":refresh_token},format="json")
                    refresh_token = response.data["refresh_token"]
                    
            url = reverse("knox_refresh")
            response = self.client.post(url,{"refresh_token":first},format="json")
            
            self.assertEqual(RefreshFamily.objects.count(), 0)

    def test_refresh_token_expiry_signal(self):
        if knox_settings.ENABLE_REFRESH_TOKEN:
            self.refresh_signal_was_called = False
            
            def handler(sender, username, **kwargs):
                self.refresh_signal_was_called = True

            refresh_token_expired.connect(handler)
            
            token_instance, token = AuthToken.objects.create(
                user=self.user,
                expiry=timedelta(seconds=-1)
            )
            refresh_instance, refresh_token = AuthRefreshToken.objects.create(
                user=self.user,
                expiry=timedelta(seconds=-1)
            )
            RefreshFamily.objects.create(
                user=self.user,
                parent=refresh_token,
                refresh_token=refresh_token,
                token=token
            )
            url = reverse("knox_refresh")
            response = self.client.post(url, {"refresh_token":refresh_token}, format='json')
            self.assertEqual(response.status_code, 401)
            self.assertTrue(self.refresh_signal_was_called)
          

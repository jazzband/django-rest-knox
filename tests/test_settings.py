import hashlib
from datetime import timedelta
from unittest import mock

from django.core.signals import setting_changed
from django.test import override_settings

from knox.settings import (
    CONSTANTS, IMPORT_STRINGS, knox_settings, reload_api_settings,
)


class TestKnoxSettings:
    @override_settings(REST_KNOX={
        'AUTH_TOKEN_CHARACTER_LENGTH': 32,
        'TOKEN_TTL': timedelta(hours=5),
        'AUTO_REFRESH': True,
    })
    def test_override_settings(self):
        """
        Test that settings can be overridden.
        """
        assert knox_settings.AUTH_TOKEN_CHARACTER_LENGTH == 32
        assert knox_settings.TOKEN_TTL == timedelta(hours=5)
        assert knox_settings.AUTO_REFRESH is True
        # Default values should remain unchanged
        assert knox_settings.AUTH_HEADER_PREFIX == 'Token'

    def test_constants_immutability(self):
        """
        Test that CONSTANTS cannot be modified.
        """
        with self.assertRaises(Exception):
            CONSTANTS.TOKEN_KEY_LENGTH = 20

        with self.assertRaises(Exception):
            CONSTANTS.DIGEST_LENGTH = 256

    def test_constants_values(self):
        """
        Test that CONSTANTS have correct values.
        """
        assert CONSTANTS.TOKEN_KEY_LENGTH == 15
        assert CONSTANTS.DIGEST_LENGTH == 128
        assert CONSTANTS.MAXIMUM_TOKEN_PREFIX_LENGTH == 10

    def test_reload_api_settings(self):
        """
        Test settings reload functionality.
        """
        new_settings = {
            'TOKEN_TTL': timedelta(hours=2),
            'AUTH_HEADER_PREFIX': 'Bearer',
        }

        reload_api_settings(
            setting='REST_KNOX',
            value=new_settings
        )

        assert knox_settings.TOKEN_TTL == timedelta(hours=2)
        assert knox_settings.AUTH_HEADER_PREFIX == 'Bearer'

    def test_token_prefix_length_validation(self):
        """
        Test that TOKEN_PREFIX length is validated.
        """
        with self.assertRaises(ValueError, match="Illegal TOKEN_PREFIX length"):
            reload_api_settings(
                setting='REST_KNOX',
                value={'TOKEN_PREFIX': 'x' * 11}  # Exceeds MAXIMUM_TOKEN_PREFIX_LENGTH
            )

    def test_import_strings(self):
        """
        Test that import strings are properly handled.
        """
        assert 'SECURE_HASH_ALGORITHM' in IMPORT_STRINGS
        assert 'USER_SERIALIZER' in IMPORT_STRINGS

    @override_settings(REST_KNOX={
        'SECURE_HASH_ALGORITHM': 'hashlib.md5'
    })
    def test_hash_algorithm_import(self):
        """
        Test that hash algorithm is properly imported.
        """
        assert knox_settings.SECURE_HASH_ALGORITHM == hashlib.md5

    def test_setting_changed_signal(self):
        """
        Test that setting_changed signal properly triggers reload.
        """
        new_settings = {
            'TOKEN_TTL': timedelta(hours=3),
        }

        setting_changed.send(
            sender=None,
            setting='REST_KNOX',
            value=new_settings
        )

        assert knox_settings.TOKEN_TTL == timedelta(hours=3)

    @mock.patch('django.conf.settings')
    def test_custom_token_model(self, mock_settings):
        """
        Test custom token model setting.
        """
        custom_model = 'custom_app.CustomToken'
        mock_settings.KNOX_TOKEN_MODEL = custom_model

        # Reload settings
        reload_api_settings(
            setting='REST_KNOX',
            value={}
        )

        assert knox_settings.TOKEN_MODEL == custom_model

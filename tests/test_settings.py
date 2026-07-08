import hashlib
from datetime import timedelta

from django.test import SimpleTestCase, TestCase, override_settings

from knox.settings import CONSTANTS, IMPORT_STRINGS, knox_settings


class TestKnoxSettings(TestCase):
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

    @override_settings(REST_KNOX={
        'TOKEN_TTL': timedelta(hours=2),
        'AUTH_HEADER_PREFIX': 'Bearer',
    })
    def test_reload_api_settings(self):
        """
        Test settings reload functionality via override_settings.
        """
        assert knox_settings.TOKEN_TTL == timedelta(hours=2)
        assert knox_settings.AUTH_HEADER_PREFIX == 'Bearer'

    def test_token_prefix_length_validation(self):
        """
        Test that TOKEN_PREFIX length is validated.
        """
        with self.assertRaisesRegex(ValueError, "Illegal TOKEN_PREFIX length"):
            with override_settings(REST_KNOX={'TOKEN_PREFIX': 'x' * 11}):
                pass

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
        with override_settings(REST_KNOX={'TOKEN_TTL': timedelta(hours=3)}):
            assert knox_settings.TOKEN_TTL == timedelta(hours=3)
        assert knox_settings.TOKEN_TTL == timedelta(hours=10)

    def test_custom_token_model(self):
        """
        Test that TOKEN_MODEL defaults to knox.AuthToken.
        """
        assert knox_settings.TOKEN_MODEL == 'knox.AuthToken'


class TestSettingsObjectIdentity(SimpleTestCase):
    """
    Regression test: knox_settings object identity must survive reload.
    Previously, reload_api_settings rebound the module global to a new
    APISettings object, leaving stale references in modules that did
    ``from knox.settings import knox_settings``.
    """

    def test_object_identity_survives_reload(self):
        from knox.settings import knox_settings as ks_from_import
        original_id = id(ks_from_import)

        with override_settings(REST_KNOX={'TOKEN_TTL': timedelta(hours=1)}):
            assert id(ks_from_import) == original_id
            assert ks_from_import.TOKEN_TTL == timedelta(hours=1)

        assert id(ks_from_import) == original_id
        assert ks_from_import.TOKEN_TTL == timedelta(hours=10)

    def test_values_change_after_reload(self):
        with override_settings(REST_KNOX={'TOKEN_TTL': timedelta(hours=2)}):
            assert knox_settings.TOKEN_TTL == timedelta(hours=2)
        assert knox_settings.TOKEN_TTL == timedelta(hours=10)

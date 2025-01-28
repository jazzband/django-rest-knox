from unittest.mock import patch

from django.test import TestCase

from knox.crypto import create_token_string, hash_token, make_hex_compatible
from knox.settings import knox_settings


class CryptoUtilsTestCase(TestCase):
    def test_create_token_string(self):
        """
        Verify token string creation has correct length and contains only hex characters.
        """
        with patch('os.urandom') as mock_urandom:
            mock_urandom.return_value = b'abcdef1234567890'
            expected_length = knox_settings.AUTH_TOKEN_CHARACTER_LENGTH
            token = create_token_string()
            self.assertEqual(len(token), expected_length)
            hex_chars = set('0123456789abcdef')
            self.assertTrue(all(c in hex_chars for c in token.lower()))

    def test_make_hex_compatible_with_valid_input(self):
        """
        Ensure standard strings are correctly converted to hex-compatible bytes.
        """
        test_token = "test123"
        result = make_hex_compatible(test_token)
        self.assertIsInstance(result, bytes)
        expected = b'test123'
        self.assertEqual(result, expected)

    def test_make_hex_compatible_with_empty_string(self):
        """
        Verify empty string input returns empty bytes.
        """
        test_token = ""
        result = make_hex_compatible(test_token)
        self.assertEqual(result, b'')

    def test_make_hex_compatible_with_special_characters(self):
        """
        Check hex compatibility conversion handles special characters correctly.
        """
        test_token = "test@#$%"
        result = make_hex_compatible(test_token)
        self.assertIsInstance(result, bytes)
        expected = b'test@#$%'
        self.assertEqual(result, expected)

    def test_hash_token_with_valid_token(self):
        """
        Verify hash output is correct length and contains valid hex characters.
        """
        test_token = "abcdef1234567890"
        result = hash_token(test_token)
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 128)
        hex_chars = set('0123456789abcdef')
        self.assertTrue(all(c in hex_chars for c in result.lower()))

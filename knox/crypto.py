import binascii

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from OpenSSL.rand import bytes as generate_bytes

from knox.settings import knox_settings, CONSTANTS

sha = knox_settings.SECURE_HASH_ALGORITHM


def create_token_string():
    return binascii.hexlify(
        generate_bytes(int(knox_settings.AUTH_TOKEN_CHARACTER_LENGTH / 2))
    ).decode()


def create_salt_string():
    return binascii.hexlify(
        generate_bytes(int(CONSTANTS.SALT_LENGTH / 2))).decode()


def hash_token(token, salt):
    '''
    Calculates the hash of a token and salt.
    input is unhexlified
    '''
    digest = hashes.Hash(sha(), backend=default_backend())
    digest.update(binascii.unhexlify(token))
    digest.update(binascii.unhexlify(salt))
    return binascii.hexlify(digest.finalize()).decode()

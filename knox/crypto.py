import binascii
from os import urandom as generate_bytes

from knox.settings import knox_settings

hash_func = knox_settings.SECURE_HASH_ALGORITHM


def create_token_string():
    return binascii.hexlify(
        generate_bytes(int(knox_settings.AUTH_TOKEN_CHARACTER_LENGTH / 2))
    ).decode()


def hash_token(token: str) -> str:
    """
    Calculates the hash of a token.
    Token must contain an even number of hex digits or
    a binascii.Error exception will be raised.
    """
    digest = hash_func()
    digest.update(binascii.unhexlify(token))
    return digest.hexdigest()

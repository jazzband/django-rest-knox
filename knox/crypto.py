import binascii
from os import urandom as generate_bytes

from knox.settings import knox_settings

hash_func = knox_settings.SECURE_HASH_ALGORITHM


def create_token_string() -> str:
    return binascii.hexlify(
        generate_bytes(int(knox_settings.AUTH_TOKEN_CHARACTER_LENGTH / 2))
    ).decode()


def make_hex_compatible(token: str) -> bytes:
    """
    We need to make sure that the token, that is send is hex-compatible.
    When a token prefix is used, we cannot guarantee that.
    """
    return binascii.unhexlify(binascii.hexlify(bytes(token, 'utf-8')))


def hash_token(token: str) -> str:
    """
    Calculates the hash of a token.
    Token must contain an even number of hex digits or
    a binascii.Error exception will be raised.
    """
    digest = hash_func()
    digest.update(make_hex_compatible(token))
    return digest.hexdigest()

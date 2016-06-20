import binascii
import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf import pbkdf2
from OpenSSL.rand import bytes as generate_bytes

from django.utils import encoding

from knox.settings import knox_settings, CONSTANTS

sha = knox_settings.SECURE_HASH_ALGORITHM

def create_token_string():
    return (
        binascii.hexlify(
            generate_bytes(
                int(knox_settings.AUTH_TOKEN_CHARACTER_LENGTH/2)
            )
        ).decode())

def create_salt_string():
    return (
        binascii.hexlify(
            generate_bytes(
                int(CONSTANTS.SALT_LENGTH/2)
            )
        ).decode())

def hash_token(token, salt):
    '''
    Calculates the hash of a token and salt.
    input is unhexlified
    '''
    digest = hashes.Hash(sha(), backend=default_backend())
    digest.update(binascii.unhexlify(token))
    digest.update(binascii.unhexlify(salt))
    return binascii.hexlify(digest.finalize()).decode()


def derive_fernet_key(password, salt):
    """Derive a secure Fernet key from arbitrary input password."""
    kdf = pbkdf2.PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=encoding.force_bytes(salt),
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(
        encoding.force_bytes(password)))

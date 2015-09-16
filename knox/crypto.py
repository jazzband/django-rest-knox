from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from OpenSSL.rand import bytes as generate_bytes

from knox.settings import knox_settings

sha = knox_settings.SECURE_HASH_ALGORITHM

def hash_token(token, salt):
    '''
    Calculates the hash of a token and salt.
    Both the provided token and salt should be byte objects
    '''
    digest = hashes.Hash(sha(), backend=default_backend())
    digest.update(token)
    digest.update(salt)
    return digest.finalize()

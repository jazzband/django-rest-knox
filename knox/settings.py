from datetime import timedelta

from django.conf import settings
from django.core.signals import setting_changed
from rest_framework.settings import APISettings, api_settings

DEFAULTS = {
    'SECURE_HASH_ALGORITHM': 'hashlib.sha512',
    'AUTH_TOKEN_CHARACTER_LENGTH': 64,
    'TOKEN_TTL': timedelta(hours=10),
    'USER_SERIALIZER': None,
    'TOKEN_LIMIT_PER_USER': None,
    'AUTO_REFRESH': False,
    'AUTO_REFRESH_MAX_TTL': None,
    'MIN_REFRESH_INTERVAL': 60,
    'AUTH_HEADER_PREFIX': 'Token',
    'EXPIRY_DATETIME_FORMAT': api_settings.DATETIME_FORMAT,
    'TOKEN_MODEL': getattr(settings, 'KNOX_TOKEN_MODEL', 'knox.AuthToken'),
    'TOKEN_PREFIX': '',
}

IMPORT_STRINGS = {
    'SECURE_HASH_ALGORITHM',
    'USER_SERIALIZER',
}


class KnoxSettings(APISettings):
    @property
    def user_settings(self):
        if not hasattr(self, '_user_settings'):
            self._user_settings = getattr(settings, 'REST_KNOX', {})
        return self._user_settings


knox_settings = KnoxSettings(None, DEFAULTS, IMPORT_STRINGS)


def reload_api_settings(*args, **kwargs):
    setting = kwargs['setting']
    if setting == 'REST_KNOX':
        knox_settings.reload()
        if len(knox_settings.TOKEN_PREFIX) > CONSTANTS.MAXIMUM_TOKEN_PREFIX_LENGTH:
            raise ValueError("Illegal TOKEN_PREFIX length")


setting_changed.connect(reload_api_settings)


class CONSTANTS:
    '''
    Constants cannot be changed at runtime
    '''
    TOKEN_KEY_LENGTH = 15
    DIGEST_LENGTH = 128
    MAXIMUM_TOKEN_PREFIX_LENGTH = 10

    def __setattr__(self, *args, **kwargs):
        raise Exception('''
            Constant values must NEVER be changed at runtime, as they are
            integral to the structure of database tables
            ''')


CONSTANTS = CONSTANTS()  # type: ignore

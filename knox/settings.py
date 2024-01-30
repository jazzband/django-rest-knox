from datetime import timedelta
from django.conf import settings
from django.test.signals import setting_changed
from rest_framework.settings import APISettings, api_settings

USER_SETTINGS = getattr(settings, 'REST_KNOX', None)

DEFAULTS = {
    'SECURE_HASH_ALGORITHM': 'hashlib.sha512',
    'AUTH_TOKEN_CHARACTER_LENGTH': 64,
    'TOKEN_TTL': timedelta(hours=10),
    'USER_SERIALIZER': None,
    'TOKEN_LIMIT_PER_USER': None,
    'AUTO_REFRESH': False,
    'MIN_REFRESH_INTERVAL': 60,
    'AUTH_HEADER_PREFIX': 'Token',
    'EXPIRY_DATETIME_FORMAT': api_settings.DATETIME_FORMAT,
    'TOKEN_MODEL': getattr(settings, 'KNOX_TOKEN_MODEL', 'knox.AuthToken'),
    'TOKEN_PREFIX': '',
    
    'ENABLE_REFRESH_TOKEN': False,
    'REFRESH_TOKEN_MODEL': getattr(settings, 'KNOX_REFRESH_TOKEN_MODEL', 'knox.AuthRefreshToken'),
    'REFRESH_FAMILY_MODEL': getattr(settings, 'KNOX_REFRESH_FAMILY_MODEL', 'knox.RefreshFamily'),
    "REFRESH_TOKEN_TTL" : timedelta(days=30),
    'MAX_TOKEN_HISTORY': 10
}

IMPORT_STRINGS = {
    'SECURE_HASH_ALGORITHM',
    'USER_SERIALIZER',
}

knox_settings = APISettings(USER_SETTINGS, DEFAULTS, IMPORT_STRINGS)


def reload_api_settings(*args, **kwargs):
    global knox_settings
    setting, value = kwargs['setting'], kwargs['value']
    if setting == 'REST_KNOX':
        knox_settings = APISettings(value, DEFAULTS, IMPORT_STRINGS)
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

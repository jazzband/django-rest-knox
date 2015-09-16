from django.conf import settings
from django.test.signals import setting_changed
from rest_framework.settings import APISettings

USER_SETTINGS = getattr(settings, 'REST_KNOX', None)

DEFAULTS = {
    'SECURE_HASH_ALGORITHM': 'cryptography.hazmat.primitives.hashes.SHA512'
}

IMPORT_STRINGS = (
    'SECURE_HASH_ALGORITHM',
)

knox_settings = APISettings(USER_SETTINGS, DEFAULTS, IMPORT_STRINGS)

def reload_api_settings(*args, **kwargs):
    global knox_settings
    setting, value = kwargs['setting'], kwargs['value']
    if setting == 'REST_KNOX':
        knox_settings = APISettings(value, DEFAULTS, IMPORT_STRINGS)

setting_changed.connect(reload_api_settings)

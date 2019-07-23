from knox.settings import knox_settings


def get_token_model():
    if knox_settings.TOKEN_MODEL:
        return knox_settings.TOKEN_MODEL
    from knox.models import AuthToken
    return AuthToken

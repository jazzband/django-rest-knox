from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from knox.settings import knox_settings


def get_token_model():
    """
    Return the AuthToken model that is active in this project.
    """

    try:
        return apps.get_model(knox_settings.TOKEN_MODEL, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(
            "TOKEN_MODEL must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "TOKEN_MODEL refers to model '%s' that has not been installed"
            % knox_settings.TOKEN_MODEL
        )

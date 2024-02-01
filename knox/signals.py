import django.dispatch

token_expired = django.dispatch.Signal()
refresh_token_expired = django.dispatch.Signal()

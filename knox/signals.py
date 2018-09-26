import django.dispatch

token_expired = django.dispatch.Signal(providing_args=["username", "source"])

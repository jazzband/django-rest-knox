try:
    # For django >= 2.0
    from django.urls import include, path
except ImportError:
    # For django < 2.0
    from django.conf.urls import include, url
    path = url

from .views import RootView

urlpatterns = [
    path(r'^api/', include('knox.urls')),
    path(r'^api/$', RootView.as_view(), name="api-root"),
]

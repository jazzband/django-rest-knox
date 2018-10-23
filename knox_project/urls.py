try:
    # For django >= 2.0
    from django.urls import include, re_path
except ImportError:
    # For django < 2.0
    from django.conf.urls import include, url
    re_path = url

from .views import RootView

urlpatterns = [
    re_path(r'^api/', include('knox.urls')),
    re_path(r'^api/$', RootView.as_view(), name="api-root"),
]

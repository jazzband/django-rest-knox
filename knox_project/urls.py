from django.conf.urls import include, url

from .views import RootView

urlpatterns = [
    url(r'^api/', include('knox.urls')),
    url(r'^api/$', RootView.as_view(), name="api-root"),
]

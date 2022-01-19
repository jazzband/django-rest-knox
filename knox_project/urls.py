from django.urls import include, re_path, path

from .views import RootView

urlpatterns = [
    path('', include('lib.urls')),
    re_path(r'^api/', include('knox.urls')),
    re_path(r'^api/$', RootView.as_view(), name="api-root"),
]

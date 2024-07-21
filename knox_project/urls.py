from django.contrib import admin
from django.urls import include, re_path

from .views import RootView

urlpatterns = [
    re_path(r'^api/', include('knox.urls')),
    re_path(r'^api/$', RootView.as_view(), name="api-root"),
    re_path(r'^admin/', admin.site.urls),
]

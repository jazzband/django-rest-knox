from django.urls import include, path
from .views import RootView

urlpatterns = [
    path(r'^api/', include('knox.urls')),
    path(r'^api/$', RootView.as_view(), name="api-root"),
]

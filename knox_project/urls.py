from django.urls import include, path

from .views import RootView

urlpatterns = [
    path('api/', include('knox.urls')),
    path('api/', RootView.as_view(), name="api-root"),
]

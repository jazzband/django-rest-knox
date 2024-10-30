from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from .views import RootView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('knox.urls')),
    path('api/', RootView.as_view(), name="api-root"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

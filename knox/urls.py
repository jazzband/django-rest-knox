from django.conf.urls import include, url

from knox import views

urlpatterns = [
    url(r'', views.LogoutView.as_view()),
]

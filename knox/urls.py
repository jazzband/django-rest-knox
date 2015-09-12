from django.conf.urls import include, url

from knox import views

urlpatterns = [
    url(r'login/', views.LoginView.as_view()),
    url(r'logout/', views.LogoutView.as_view()),
]

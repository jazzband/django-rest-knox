from django.conf.urls import include, url

from knox import views

urlpatterns = [
    url(r'login/', views.LoginView.as_view(), name='knox_login'),
    url(r'logout/', views.LogoutView.as_view(), name='knox_logout'),
    url(r'logoutall/', views.LogoutAllView.as_view(), name='knox_logoutall'),
]

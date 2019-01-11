from django.conf.urls import url

from knox import views

urlpatterns = [
    url(r'login/', views.LoginView.as_view(), name='knox_login'),
    url(r'logout/$', views.LogoutView.as_view(), name='knox_logout'),
    url(r'logout/all/$', views.LogoutAllView.as_view(), name='knox_logout_all'),
    url(r'refresh/$', views.TokenRefreshView.as_view(), name='knox_refresh')
]

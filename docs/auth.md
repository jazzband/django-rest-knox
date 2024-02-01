# Authentication `knox.auth`

Knox provides one class to handle authentication.

## TokenAuthentication

This works using [DRF's authentication system](https://www.django-rest-framework.org/api-guide/authentication/).

Knox tokens should be generated using the provided views.
Any `APIView` or `ViewSet` can be accessed using these tokens by adding `TokenAuthentication`
to the View's `authentication_classes`.
To authenticate, the `Authorization` header should be set on the request, with a
value of the word `"Token"`, then a space, then the authentication token provided by
`LoginView`.

Example:
```python
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from knox.auth import TokenAuthentication

class ExampleView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        content = {
            'foo': 'bar'
        }
        return Response(content)
```

Example auth header:

```javascript
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b9836F45E23A345
```

Tokens expire after a preset time. See settings.


### Global usage on all views

You can activate TokenAuthentication on all your views by adding it to `REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]`. 

If it is your only default authentication class, remember to overwrite knox's LoginView, otherwise it'll not work, since the login view will require a authentication token to generate a new token, rendering it unusable.

For instance, you can authenticate users using Basic Authentication by simply overwriting knox's LoginView and setting BasicAuthentication as one of the acceptable authentication classes, as follows: 

**views.py:**
```python
from knox.views import LoginView as KnoxLoginView
from rest_framework.authentication import BasicAuthentication

class LoginView(KnoxLoginView):
    authentication_classes = [BasicAuthentication]
```

**urls.py:**
```python
from knox import views as knox_views
from yourapp.api.views import LoginView

urlpatterns = [
     path(r'login/', LoginView.as_view(), name='knox_login'),
     path(r'refresh/',knox_views.RefreshTokenView.as_view(),name='knox_refresh'), 
     path(r'logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
     path(r'logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),
]
```

You can use any number of authentication classes if you want to be able to authenticate using different methods (eg.: Basic and JSON) in the same view. Just be sure not to set TokenAuthentication as your only authentication class on the login view.

If you decide to use Token Authentication as your only authentication class, you can overwrite knox's login view as such:

**views.py:**
```python
from django.contrib.auth import login

from rest_framework import permissions
from rest_framework.authtoken.serializers import AuthTokenSerializer
from knox.views import LoginView as KnoxLoginView

class LoginView(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return super(LoginView, self).post(request, format=None)
```

**urls.py:**
```python
from knox import views as knox_views
from yourapp.api.views import LoginView

urlpatterns = [
     path(r'login/', LoginView.as_view(), name='knox_login'),
     path(r'refresh/',knox_views.RefreshTokenView.as_view(),name='knox_refresh'), 
     path(r'logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
     path(r'logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),
]
```

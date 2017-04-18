# Authentication `knox.auth`

Knox provides one class to handle authentication.

## TokenAuthentication

This works using [DRF's authentication system](http://www.django-rest-framework.org/api-guide/authentication/).

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

You can activate TokenAuthentication on all your views by adding it to
`REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]`. If it is your only
authentication class remember to overwrite the login view and url as at least
the token-obtaining view may not require a token:

```python

views.py:

from knox.views import LoginView as KnoxLoginView
from rest_framework.authentication import BasicAuthentication

class LoginView(KnoxLoginView):
    authentication_classes = [BasicAuthentication]

urls.py:

from knox import views as knox_views
from yourapp.api.views import LoginView

urlpatterns = [
     url(r'login/', LoginView.as_view(), name='knox_login'),
     url(r'logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
     url(r'logoutall/', knox_views.LogoutAllView.as_view()),
]
```

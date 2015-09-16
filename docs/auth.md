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

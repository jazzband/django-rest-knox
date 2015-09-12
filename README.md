# django-rest-knox
[![Build Status](https://travis-ci.org/James1345/django-rest-knox.svg?branch=develop)](https://travis-ci.org/James1345/django-rest-knox)

Authentication Module for django rest auth

Knox provides easy to use authentication for [Django REST Framework](http://www.django-rest-framework.org/)
The aim is to allow for common patterns in applications that are REST based,
with little extra effort; and to ensure that connections remain secure.

Knox Authentication is token based, similar to the `TokenAuthentication` built
in to DRF. However, it overcomes some problems present in the default implementation:

- DRF Tokens are generated with `os.urandom`, which is not cryptographically
  secure.
  Knox uses OpenSSL to provide tokens.
- DRF tokens are limitted to one per user. This does not facilitate securely
  signing in from multiple devices, as the token is shared. It also requires
  *all* devices to be logged out if a server-side logout is required (i.e. the
  token is deleted).
  Knox provides one token per call to the login view - allowing
  each client to have its own token which is deleted on the server side when the client
  logs out.
  Knox also provides an option for a logged in client to remove *all* tokens
  that the server has - forcing all clients to re-authenticate.

## Installation

### Requirements

Knox depends on `cryptography` to provide bindings to `OpenSSL` for token generation
This requires the OpenSSL build libraries to be available.

#### Windows
Cryptography is a statically linked build, no extra steps are needed

#### Linux
`cryptography` should build very easily on Linux provided you have a C compiler,
headers for Python (if you’re not using `pypy`), and headers for the OpenSSL and
`libffi` libraries available on your system.

Debian and Ubuntu:
```bash
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev python-dev
```

Fedora and RHEL-derivatives:
```bash
sudo yum install gcc libffi-devel python-devel openssl-devel
```
For other systems or problems, see the [cryptography installation docs](https://cryptography.io/en/latest/installation/)

### Installing Knox
Knox should be installed with pip

```bash
pip install django-rest-knox
```

add `rest_framework` and `knox` to your `INSTALLED_APPS`

```python
INSTALLED_APPS = (
  ...
  rest_framework,
  knox,
  ...
)
```

Remember to apply the migrations for the models

```bash
python manage.py migrate
```

## Usage

### Views
Knox achieves most of its functionality through three views.
These can easily be included via your url config:

```python
urlpatterns = [
  #...snip...
  url(r'api/auth/', include('knox.urls'))
  #...snip...
]
```
**N.B.** it is important to use the string sintax and not try to import knox.urls,
as the reference to the User model will cause the app to fail at import time.

The views would then acessible as:

- `/api/auth/login` -> `LoginView`
- `/api/auth/logout` -> `LogoutView`
- `/api/auth/logoutall` -> `LogoutAllView`

they can also be looked up by name:

```python
reverse('knox_login')
reverse('knox_logout')
reverse('knox_logoutall')
```

#### LoginView
This view accepts only a post request with an empty body. It responds only to HTTP Basic authentication.
When it receives an authenticated request, it will return json
- `user` an object representing the user that was authenticated
- `token` the token that should be used for other requests

#### LogoutView
This view accepts only a post request with an empty body. It responds to Knox Token
Authentication. On a successful request, the token used to authenticate is deleted from the
system and can no longer be used to authenticate.

#### LogoutAllView
This view accepts only a post request with an empty body. It responds to Knox Token
Authentication. On a successful request, the token used to authenticate, and *all other tokens*
registered to the same `User` account, are deleted from the
system and can no longer be used to authenticate.

### Authentication Classes
Knox provides one class for authentication - `TokenAuthentication`
This works in using the same way as [DRF's authentication system](http://www.django-rest-framework.org/api-guide/authentication/).

Knox tokens should be generated using the provided views.
Any `APIView` or `ViewSet` can be accessed using these tokens by adding `TokenAuthentication`
to the classes `authentication_classes`.
To authenticate, the `Authorization` header should be set on the request, with a
value of the word 'Token', then a space, then the authentication token provided by
`LoginView`.

Example:
```python
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from knox.auth import TokenAuthentication

class ExampleView(APIView):
    authentication_classes = (TokenAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        content = {
            'user': unicode(request.user),  # `django.contrib.auth.User` instance.
            'auth': unicode(request.auth),  # None
        }
        return Response(content)
```

Example auth header:

```javascript
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b9836F45E23A345
```

# Settings `knox.settings`

Settings in Knox are handled in a similar way to the rest framework settings.
All settings are namespaced in the `'REST_KNOX'` setting.

Example `settings.py`

```python
#...snip...
# These are the default values if none are set
from datetime import timedelta
from rest_framework.settings import api_settings

KNOX_TOKEN_MODEL = 'knox.AuthToken'

REST_KNOX = {
  'SECURE_HASH_ALGORITHM': 'hashlib.sha512',
  'AUTH_TOKEN_CHARACTER_LENGTH': 64,
  'TOKEN_TTL': timedelta(hours=10),
  'USER_SERIALIZER': 'knox.serializers.UserSerializer',
  'TOKEN_LIMIT_PER_USER': None,
  'AUTO_REFRESH': False,
  'MIN_REFRESH_INTERVAL': 60,
  'AUTH_HEADER_PREFIX': 'Token',
  'EXPIRY_DATETIME_FORMAT': api_settings.DATETIME_FORMAT,
  'TOKEN_MODEL': 'knox.AuthToken',
}
#...snip...
```

## KNOX_TOKEN_MODEL
This is the variable used in the swappable dependency of the `AuthToken` model

## SECURE_HASH_ALGORITHM
This is a reference to the class used to provide the hashing algorithm for
token storage.

*Do not change this unless you know what you are doing*

By default, Knox uses SHA-512 to hash tokens in the database.

`hashlib.sha3_512` is an acceptable alternative setting for production use.

### Tests
SHA-512 and SHA3-512 are secure, however, they are slow. This should not be a
problem for your users, but when testing it may be noticeable (as test cases tend
to use many more requests much more quickly than real users). In testing scenarios
it is acceptable to use `MD5` hashing (`hashlib.md5`).

MD5 is **not secure** and must *never* be used in production sites.

## AUTH_TOKEN_CHARACTER_LENGTH
This is the length of the token that will be sent to the client. By default it
is set to 64 characters (this shouldn't need changing).

## TOKEN_TTL
This is how long a token can exist before it expires. Expired tokens are automatically
removed from the system.

The setting should be set to an instance of `datetime.timedelta`. The default is
10 hours ()`timedelta(hours=10)`).

Setting the TOKEN_TTL to `None` will create tokens that never expire.

Warning: setting a 0 or negative timedelta will create tokens that instantly expire,
the system will not prevent you setting this.

## TOKEN_LIMIT_PER_USER
This allows you to control how many valid tokens can be issued per user.
If the limit for valid tokens is reached, an error is returned at login.
By default this option is disabled and set to `None` -- thus no limit.

## USER_SERIALIZER
This is the reference to the class used to serialize the `User` objects when
successfully returning from `LoginView`. The default is `knox.serializers.UserSerializer`

## AUTO_REFRESH
This defines if the token expiry time is extended by TOKEN_TTL each time the token
is used.

## MIN_REFRESH_INTERVAL
This is the minimum time in seconds that needs to pass for the token expiry to be updated
in the database.

## AUTH_HEADER_PREFIX
This is the Authorization header value prefix. The default is `Token`

## EXPIRY_DATETIME_FORMAT
This is the expiry datetime format returned in the login view. The default is the
[DATETIME_FORMAT][DATETIME_FORMAT] of Django REST framework. May be any of `None`, `iso-8601`
or a Python [strftime format][strftime format] string.

## TOKEN_MODEL
This is the reference to the model used as `AuthToken`. We can define a custom `AuthToken`
model in our project that extends `knox.AbstractAuthToken` and add our business logic to it.
The default is `knox.AuthToken`

[DATETIME_FORMAT]: https://www.django-rest-framework.org/api-guide/settings/#date-and-time-formatting
[strftime format]: https://docs.python.org/3/library/time.html#time.strftime

## TOKEN_PREFIX
This is the prefix for the generated token that is used in the Authorization header. The default is just an empty string.
It can be up to `CONSTANTS.MAXIMUM_TOKEN_PREFIX_LENGTH` long.
## ENABLE_COOKIE_AUTH
This defines if the authentication will be done using a `HTTP-only` Cookie.
The default is `False`
## AUTH_COOKIE_SALT
This is the Salt `(String)` that is added to better store and secure token value inside Cookies
the default value is `"knox"` and it can be up to `CONSTANTS.MAXIMUM_SALT_LENGTH` long.
## AUTH_COOKIE_KEY
This is the `Cookie` key of the token. The default is `knox`.
It can be up to `CONSTANTS.MAXIMUM_COOKIE_KEY_LENGTH` long.

# Constants `knox.settings`
Knox also provides some constants for information. These must not be changed in
external code; they are used in the model definitions in knox and an error will
be raised if there is an attempt to change them.

```python
from knox.settings import CONSTANTS

print(CONSTANTS.DIGEST_LENGTH) #=> 128
```

## DIGEST_LENGTH
This is the length of the digest that will be stored in the database for each token.

## MAXIMUM_TOKEN_PREFIX_LENGTH
This is the maximum length of the token prefix.

## MAXIMUM_COOKIE_KEY_LENGTH
This is the maximum length of the cookie `key`

## MAXIMUM_SALT_LENGTH
This is the maximum length of  Salt `(String)` that encode token value inside the cookie.

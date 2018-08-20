######
3.3.0
######
- **Breaking changes**: Successful authentication **ONLY** returns `Token` object by default now. `USER_SERIALIZER` must be overridden to return custom data. This also removes hardcoded user fields from `UserSerializer` class to allow more generic behaivor by default.

######
3.2.0
######
- Introduce new setting AUTO_REFRESH for controlling if token expiry time should be extended automatically

######
3.1.5
######
- Make AuthTokenAdmin more compatible with big user tables
- Extend docs regarding usage of Token Authentication as single authentication method.

######
3.1.4
######
- Fix compability with django-rest-swagger (bad inheritance)

######
3.1.3
######
- Avoid 500 error response for invalid-length token requests

######
3.1.2
######
- restore compability with Python <2.7.7

######
3.1.1
######
- use hmac.compare_digest instead of == for comparing hashes for more security

######
3.1.0
######
- drop Django 1.8 support as djangorestframework did so too in v.3.7.0
- build rest-knox on Django 1.11 and 2.0

######
3.0.3
######
- drop using OpenSSL in favor of urandom

######
3.0.2
######
- Add context to UserSerializer
- improve docs

######
3.0.1
######
- improved docs and readme
- login response better supporting hyperlinked fields

######
3.0.3
######
- drop using OpenSSL in favor of urandom

######
3.0.2
######
- Add context to UserSerializer
- improve docs

######
3.0.1
######
- improved docs and readme
- login response better supporting hyperlinked fields

######
3.0.0
######
**Please be aware: updating to this version requires applying a database migration. All clients will need to reauthenticate.**

- Big performance fix: Introduction of token_key field to avoid having to compare a login request's token against each and every token in the database (issue #21)
- increased test coverage

######
2.2.2
######
- Bugfix: invalid token length does no longer trigger a server error
- Extending documentation

######
2.2.1
######
**Please be aware: updating to this version requires applying a database migration**

- Introducing token_key to avoid loop over all tokens on login-requests
- Signals are sent on login/logout
- Test for invalid token length
- Cleanup in code and documentation

######
2.2.0
######

- Change to support python 2.7

# Settings `knox.settings`

Settings in Knox are handled in a similar way to the rest framework settings.
All settings are namespaced in the `'REST_KNOX'` setting.

Example `settings.py`

```python
#...snip...
# These are the default values if none are set
from datetime import timedelta
'REST_KNOX' = {
  'SECURE_HASH_ALGORITHM': 'cryptography.hazmat.primitives.hashes.SHA512',
  'AUTH_TOKEN_CHARACTER_LENGTH': 64,
  'TOKEN_TTL': timedelta(hours=10),
  'USER_SERIALIZER': 'knox.serializers.UserSerializer',
}
#...snip...
```

## SECURE_HASH_ALGORITHM
This is a reference to the class used to provide the hashing algorithm for
token storage.

*Do not change this unless you know what you are doing*

By default, Knox uses SHA-512 to hash tokens in the database.

`cryptography.hazmat.primitives.hashes.Whirlpool` is an acceptable alternative setting
for production use.

### Tests
SHA-512 and Whirlpool are secure, however, they are slow. This should not be a
problem for your users, but when testing it may be noticable (as test cases tend
to use many more requests much more quickly than real users). In testing scenarios
it is acceptable to use `MD5` hashing.(`cryptography.hazmat.primitives.hashes.MD5`)

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

## USER_SERIALIZER
This is the reference to the class used to serialize the `User` objects when
succesfully returning from `LoginView`. The default is `knox.serializers.UserSerializer`

# Constants `knox.settings`
Knox also provides some constants for information. These must not be changed in
external code; they are used in the model definitions in knox and an error will
be raised if there is an attempt to change them.

```python
from knox.settings import CONSTANTS

print(CONSTANTS.DIGEST_LENGTH) #=> 128
print(CONSTANTS.SALT_LENGTH) #=> 16
```

## DIGEST_LENGTH
This is the length of the digest that will be stored in the database for each token.

## SALT_LENGTH
This is the length of the [salt][salt] that will be stored in the database for each token.

[salt]: https://en.wikipedia.org/wiki/Salt_(cryptography)

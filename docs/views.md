# Views `knox.views`
Knox provides three views that handle token management for you.

## LoginView
This view accepts only a post request with an empty body.

The LoginView accepts the same sort of authentication as your Rest Framework
`DEFAULT_AUTHENTICATION_CLASSES` setting. If this is not set, it defaults to
`(SessionAuthentication, BasicAuthentication)`.

LoginView was designed to work well with Basic authentication, or similar
schemes. If you would like to use a different authentication scheme to the
default, you can extend this class to provide your own value for
`authentication_classes`

It is possible to customize LoginView behaviour by overriding the following
helper methods:
- `get_context`, to change the context passed to the `UserSerializer`
- `get_token_ttl`, to change the token ttl
- `get_token_limit_per_user`, to change the number of tokens available for a user
- `get_user_serializer_class`, to change the class used for serializing the user

---
When the endpoint authenticates a request, a json object will be returned 
containing the `token` key along with the actual value for the key by default.
The success response also includes a `expiry` key with a timestamp for when
the token expires.

> *This is because `USER_SERIALIZER` setting is `None` by default.*

If you wish to return custom data upon successful authentication
like `first_name`, `last_name`, and `username` then the included `UserSerializer`
class can be used inside `REST_KNOX` settings by adding `knox.serializers.UserSerializer`

---

Obviously, if your app uses a custom user model that does not have these fields,
a custom serializer must be used.

## LogoutView
This view accepts only a post request with an empty body.
It responds to Knox Token Authentication. On a successful request,
the token used to authenticate is deleted from the
system and can no longer be used to authenticate.

## LogoutAllView
This view accepts only a post request with an empty body. It responds to Knox Token
Authentication.
On a successful request, the token used to authenticate, and *all other tokens*
registered to the same `User` account, are deleted from the
system and can no longer be used to authenticate.

**Note** It is not recommended to alter the Logout views. They are designed
specifically for token management, and to respond to Knox authentication.
Modified forms of the class may cause unpredictable results.

## TokenRefreshView
This view accepts only a post request with an empty body.
On a successful request, the token used to authenticate will be refreshed and its expiry will be extended by the amount set in `TOKEN_TTL`.

The response body includes an expiry key with a timestamp that represents the token's new expiry. 

**Note**: To enable this view set `ENABLE_REFRESH_ENDPOINT` to `True`.

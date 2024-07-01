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
- `get_context(self)`, to change the context passed to the `UserSerializer`
- `get_token_ttl(self)`, to change the token ttl
- `get_token_limit_per_user(self)`, to change the number of tokens available for a user
- `get_user_serializer_class(self)`, to change the class used for serializing the user
- `get_expiry_datetime_format(self)`, to change the datetime format used for expiry
- `format_expiry_datetime(self, expiry)`, to format the expiry `datetime` object at your convenience
- `create_token(self)`, to create the `AuthToken` instance at your convenience

Finally, if none of these helper methods are sufficient, you can also override `get_post_response_data`
to return a fully customized payload.

```python
...snip...
    def get_post_response_data(self, request, token, instance):
        UserSerializer = self.get_user_serializer_class()

        data = {
            'expiry': self.format_expiry_datetime(instance.expiry),
            'token': token
        }
        if UserSerializer is not None:
            data["user"] = UserSerializer(
                request.user,
                context=self.get_context()
            ).data
        return data
...snip...
```

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

By default, this endpoint returns a HTTP 204 response on a successful request. To
customize this behavior, you can override the `get_post_response` method, for example
to include a body in the logout response and/or to modify the status code:

```python
...snip...
    def get_post_response(self, request):
        return Response({"bye-bye": request.user.username}, status=200)
...snip...
```

## LogoutAllView
This view accepts only a post request with an empty body. It responds to Knox Token
Authentication.
On a successful request, a HTTP 204 is returned and the token used to authenticate,
and *all other tokens* registered to the same `User` account, are deleted from the
system and can no longer be used to authenticate. The success response can be modified
like the `LogoutView` by overriding the `get_post_response` method.

**Note** It is not recommended to alter the Logout views. They are designed
specifically for token management, and to respond to Knox authentication.
Modified forms of the class may cause unpredictable results.

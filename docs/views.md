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

When it receives an authenticated request, it will return json
- `user` an object representing the user that was authenticated
- `token` the token that should be used for any token

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

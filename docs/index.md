# Django-Rest-Knox
Knox provides easy-to-use authentication for [Django REST Framework](https://www.django-rest-framework.org/)
The aim is to allow for common patterns in applications that are REST based,
with little extra effort; and to ensure that connections remain secure.

Knox authentication is token based, similar to the `TokenAuthentication` built
into DRF. However, it overcomes some problems present in the default implementation:

-   DRF tokens are limited to one per user. This does not facilitate securely
    signing in from multiple devices, as the token is shared. It also requires
    *all* devices to be logged out if a server-side logout is required (i.e. the
    token is deleted).

    Knox provides one token per call to the login view - allowing
    each client to have its own token which is deleted on the server side when the client
    logs out. Knox also provides an optional setting to limit the amount of tokens generated
    per user.

    Knox also provides an option for a logged in client to remove *all* tokens
    that the server has - forcing all clients to re-authenticate.

-   DRF tokens are stored unencrypted in the database. This would allow an attacker
    unrestricted access to an account with a token if the database were compromised.

    Knox tokens are only stored in an encrypted form. Even if the database were
    somehow stolen, an attacker would not be able to log in with the stolen
    credentials.

-   DRF tokens track their creation time, but have no inbuilt mechanism for tokens
    expiring. Knox tokens can have an expiry configured in the app settings (default is
    10 hours.)

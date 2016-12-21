#Changelog

## 2.2.2
- Bugfix: invalid token length does no longer trigger a server error
- Extending documentation

## 2.2.1
**Please be aware: updating to his version requires applying a database migration**

- Introducing token_key to avoid loop over all tokens on login-requests
- Signals are sent on login/logout
- Test for invalid token length
- Cleanup in code and documentation

## 2.0.0
-   Hashing of tokens on the server introduced.
-   Updating to this version will clean the AuthToken table. In real terms, this
    means all users will be forced to log in again.

## 1.1.0
-   `LoginView` changed to respect `DEFAULT_AUTHENTICATION_CLASSES`

## 1.0.0
-   Initial release

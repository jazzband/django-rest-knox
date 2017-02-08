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
**Please be aware: updating to his version requires applying a database migration**

- Introducing token_key to avoid loop over all tokens on login-requests
- Signals are sent on login/logout
- Test for invalid token length
- Cleanup in code and documentation

######
2.2.0
######

- Change to support python 2.7

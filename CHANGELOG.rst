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

#URLS `knox.urls`
Knox provides a url config ready with its three default views routed.

This can easily be included in your url config:

```python
urlpatterns = [
  #...snip...
  path(r'api/auth/', include('knox.urls'))
  #...snip...
]
```
**Note** It is important to use the string syntax and not try to import `knox.urls`,
as the reference to the `User` model will cause the app to fail at import time.

The views would then accessible as:

- `/api/auth/login` -> `LoginView`
- `/api/auth/logout` -> `LogoutView`
- `/api/auth/logoutall` -> `LogoutAllView`

they can also be looked up by name:

```python
reverse('knox_login')
reverse('knox_logout')
reverse('knox_logoutall')
```

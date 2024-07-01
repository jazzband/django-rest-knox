# Installation

## Requirements

Knox depends on pythons internal library `hashlib` to provide bindings to `OpenSSL` or uses
an internal implementation of hashing algorithms for token generation.

## Installing Knox
Knox should be installed with pip

```bash
pip install django-rest-knox
```

## Setup knox

- Add `rest_framework` and `knox` to your `INSTALLED_APPS`, remove
`rest_framework.authtoken` if you were using it.

```python
INSTALLED_APPS = (
  ...
  'rest_framework',
  'knox',
  ...
)
```

- Make knox's TokenAuthentication your default authentication class
for django-rest-framework:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('knox.auth.TokenAuthentication',),
    ...
}
```

- Add the [knox url patterns](urls.md#urls-knoxurls) to your project.

- If you set TokenAuthentication as the only default authentication class on the second step, [override knox's LoginView](auth.md#global-usage-on-all-views) to accept another authentication method and use it instead of knox's default login view.

- Apply the migrations for the models.

```bash
python manage.py migrate
```

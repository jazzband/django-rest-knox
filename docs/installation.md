# Installation

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

- Make knox's TokenAuthentication your default authentification class
for django-rest-framework:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('knox.auth.TokenAuthentication',),
    ...
}
```

- Add the [knox url patterns](urls.md#urls-knoxurls) to your project.

- Apply the migrations for the models

```bash
python manage.py migrate
```

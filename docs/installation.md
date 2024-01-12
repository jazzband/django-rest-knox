# Installation

## Requirements

Knox depends on `cryptography` to provide bindings to `OpenSSL` for token generation.
This requires the OpenSSL build libraries to be available.

### Windows
Cryptography is a statically linked build, no extra steps are needed.

### Linux
`cryptography` should build very easily on Linux provided you have a C compiler,
headers for Python (if you’re not using `pypy`), and headers for the OpenSSL and
`libffi` libraries available on your system.

Debian and Ubuntu:
```bash
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev python-dev
```

Fedora and RHEL-derivatives:
```bash
sudo yum install gcc libffi-devel python-devel openssl-devel
```
For other systems or problems, see the [cryptography installation docs](https://cryptography.io/en/latest/installation/)

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

- Apply the migrations for the models

```bash
python manage.py migrate
```

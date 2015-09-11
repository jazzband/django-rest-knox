# django-rest-knox
Authentication Module for django rest auth

## Installation

pip install django-rest-knox

add rest_framework, rest_framework.authtoken and knox to your INSTALLED_APPS

include knox urls in your urls path

## Usage

- Login accepts Http Basic Authentication and returns a user's Authtoken,
  creating a new token if necessary
- Other views use Token Authentication
- Your own views should use TokenAuthentication or SessionAuthentication (or both)
- Logout invalidates the provided token
- LogoutAll invalidates all tokens for that user

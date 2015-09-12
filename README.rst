django-rest-knox
================

.. image:: https://travis-ci.org/James1345/django-rest-knox.svg?branch=develop
   :target: https://travis-ci.org/James1345/django-rest-knox

Authentication Module for django rest auth

**Does not** use rest framework's AuthTokens. This module defines its
own token based authentication (as rest\_auth's tokens are limited to
one per user)

Installation
------------

Requirements
~~~~~~~~~~~~

Knox depends on ``cryptography`` to provide bindings to ``OpenSSL`` for
token generation This requires the OpenSSL build libraries to be
available

Debian 8:

.. code:: bash

    sudo apt-get install build-essential libssl-dev libffi-dev python3-dev python-dev

::

    pip install django-rest-knox

add ``rest_framework`` and ``knox`` to your ``INSTALLED_APPS``

.. code:: python

    INSTALLED_APPS = (
      ...
      rest_framework,
      knox,
      ...
    )

include knox urls in your urls path

Usage
-----

-  Login accepts Http Basic Authentication and returns a user's
   Authtoken, creating a new token if necessary
-  Other views use Token Authentication
-  Your own views should use TokenAuthentication or
   SessionAuthentication (or both)
-  Logout invalidates the provided token
-  LogoutAll invalidates all tokens for that user

.. .. image:: https://travis-ci.org/James1345/django-rest-knox.svg?branch=develop
   :target: https://travis-ci.org/James1345/django-rest-knox image:: https://travis-ci.org/James1345/django-rest-knox.svg?branch=develop
   :target: https://travis-ci.org/James1345/django-rest-knox

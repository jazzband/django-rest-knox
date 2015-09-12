#!/bin/sh
rm README.rst
pandoc --from=markdown --to=rst --output=README.rst README.md
sed -i 's_|Build Status|_.. image:: https://travis-ci.org/James1345/django-rest-knox.svg?branch=develop_' README.rst
sed -i 's_?branch=develop_&\n   :target: https://travis-ci.org/James1345/django-rest-knox_' README.rst

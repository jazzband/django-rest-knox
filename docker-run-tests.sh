#!/usr/bin/env bash
MOUNT_FOLDER=/django-rest-knox
docker run --rm -it -v $(pwd):$MOUNT_FOLDER -w $MOUNT_FOLDER themattrix/tox

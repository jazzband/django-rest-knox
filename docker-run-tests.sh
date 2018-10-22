#!/usr/bin/env bash
MOUNT_FOLDER=/app
docker run --rm -it -v $(pwd):$MOUNT_FOLDER -w $MOUNT_FOLDER themattrix/tox

#!/usr/bin/env bash
set -e
MOUNT_FOLDER=/app
MKDOCS_DEV_ADDR=${MKDOCS_DEV_ADDR-"0.0.0.0"}
MKDOCS_DEV_PORT=${MKDOCS_DEV_PORT-"8000"}

docker run --rm -it \
    -v $(pwd):$MOUNT_FOLDER \
    -w $MOUNT_FOLDER \
    -p $MKDOCS_DEV_PORT:$MKDOCS_DEV_PORT \
    -e MKDOCS_DEV_ADDR="$MKDOCS_DEV_ADDR:$MKDOCS_DEV_PORT" \
    squidfunk/mkdocs-material:3.2.0 $*

#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

###
TEAM_NAME=opagrp
SERVICE_NAME=tapdone
DEFAULT_IMAGE_NAME=${TEAM_NAME}/${SERVICE_NAME}
DEFAULT_IMAGE_ID=${DEFAULT_IMAGE_NAME}:latest
###

IMAGE_ID=${R_IMAGE_ID-$DEFAULT_IMAGE_ID}

BUILD_TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
BUILD_HOST="${BUILD_HOST:-$(hostname)}"
RELEASE=$IMAGE_ID
GIT_URL="$(git config --get remote.origin.url || echo none)"
GIT_SHA="$(git rev-parse HEAD || echo none)"
GIT_MESSAGE="$(git log -1 --pretty=%B || echo none)"
BUILD_USER="$LOGNAME"
CONFIG_FILE="$(ls -1 config/tapdone*.txt || echo none)"
CONFIG_HASH="$(git hash-object config/tapdone*.txt || echo none)"

cat > version.json <<END
{
    "release": "$RELEASE",
    "git-url": "$GIT_URL",
    "git-sha": "$GIT_SHA",
    "git-message": "$GIT_MESSAGE",
    "build-host": "$BUILD_HOST",
    "build-timestamp": "$BUILD_TIMESTAMP",
    "build-user": "$BUILD_USER",
    "config-file": "$CONFIG_FILE",
    "config-hash": "$CONFIG_HASH"
}
END

cat version.json

docker build  -f config/Dockerfile -t $IMAGE_ID .
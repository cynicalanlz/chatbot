#!/bin/sh

set -o errexit
set -o pipefail
set -o nounset

###
TEAM_NAME=opagrp
SERVICE_NAME=tapdone
DEFAULT_IMAGE_NAME=${TEAM_NAME}/${SERVICE_NAME}
DEFAULT_IMAGE_ID=${DEFAULT_IMAGE_NAME}:latest
###

docker rm -f ${SERVICE_NAME} || true

rm -Rf configs/ 
rm -Rf backend/.cache/
rm -Rf backend/service/__pycache__/
rm version.json
rm backend/.python-version

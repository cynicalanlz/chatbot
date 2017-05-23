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

DOCKER_PS_ID=$(docker run -d --name $SERVICE_NAME \
    -v "$(pwd)/backend/service":/app/backend/service \
    -v "$(pwd)/frontend/dist":/app/frontend/dist \
    -v "$(pwd)/configs/local":/app/configs \
    -e "GUNICORN_RELOAD=True" \
    -e "PYTHONUNBUFFERED=1" \
    -p 80:80 $DEFAULT_IMAGE_ID)

docker logs --follow $DOCKER_PS_ID
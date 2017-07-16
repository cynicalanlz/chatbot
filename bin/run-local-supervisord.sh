#!/bin/bash

set -o errexit
set -o nounset

cd ../backend && supervisord -c ../config/supervisord_local.conf
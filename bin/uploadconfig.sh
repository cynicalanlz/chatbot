#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

eval `cat config/tapdone*.txt | grep AWS_DEPLOY_ACCESS_KEY`
eval `cat config/tapdone*.txt | grep AWS_DEPLOY_SECRET_KEY`

export AWS_ACCESS_KEY_ID=$AWS_DEPLOY_ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=$AWS_DEPLOY_SECRET_KEY
export AWS_DEFAULT_REGION=us-west-2

CONFIG_BUCKET=s3://tapdone-configs

echo 
echo "Listing all files in the configs bucket..."
aws s3 ls $CONFIG_BUCKET

echo 
aws s3 cp config/tapdone*.txt $CONFIG_BUCKET/

echo 
echo "Listing updated list of files in the configs bucket..."
aws s3 ls $CONFIG_BUCKET

echo 

unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_DEFAULT_REGION
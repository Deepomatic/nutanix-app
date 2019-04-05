#!/bin/bash

set -e

ROOT=$(dirname $0)

export DOCKER_IMAGE_NAME=deepomatic/nutanix-runtime:master-10
export DEPLOYMENT_NAME=deepomatic-app
export DEEPOMATIC_RUN_VERSION=0.1.0
export DEEPOMATIC_SITE_ID=${NUTANIX_RUNTIME_SITE_ID}
export GPU_FLAG="{name: GPU_IDS, value: \"0\"}"
export IMAGE_PULL_SECRETS=""
export NATS_SERVICE=""

eval "cat <<EOF
$(<${ROOT}/../deploy/k8s-manifest.yml)
EOF
" 2> /dev/null > ${ROOT}/nutanix-manifest.yml

#!/bin/bash

set -e

TEMPLATE=$1

export DOCKER_IMAGE_NAME=deepomatic/nutanix-app:0.1.0
export NEURAL_WORKER_VERSION=deepomatic/run-neural-worker:0.2.0-rc.1
export RESOURCE_SERVER_VERSION=deepomatic/run-resource-server:0.2.0-rc.1
export DEPLOYMENT_NAME=deepomatic-app
export STORAGE_CLASS=silver
export DEEPOMATIC_APP_ID=${NUTANIX_RUNTIME_APP_ID}
export DEEPOMATIC_API_KEY=${NUTANIX_RUNTIME_API_KEY}
export DEEPOMATIC_SITE_ID=${NUTANIX_RUNTIME_SITE_ID}

eval "cat <<EOF
$(<${TEMPLATE})
EOF
" 2> /dev/null > manifest.yml

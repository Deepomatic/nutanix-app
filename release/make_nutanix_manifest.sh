#!/bin/bash

set -e

ROOT=$(dirname $0)

export DOCKER_IMAGE_NAME=deepomatic/nutanix-runtime:master-22
export DEPLOYMENT_NAME=deepomatic-app
export NEURAL_WORKER_VERSION=deepomatic/run-neural-worker:0.2.0-rc.1
export RESOURCE_SERVER_VERSION=deepomatic/run-resource-server:0.2.0-rc.1
export DEEPOMATIC_APP_ID=${NUTANIX_RUNTIME_APP_ID}
export DEEPOMATIC_API_KEY=${NUTANIX_RUNTIME_API_KEY}
export DEEPOMATIC_SITE_ID=${NUTANIX_RUNTIME_SITE_ID}
export IMAGE_PULL_SECRETS=""
export NATS_SERVICE=""

eval "cat <<EOF
$(<${ROOT}/../deploy/k8s-manifest.yml)
EOF
" 2> /dev/null > ${ROOT}/nutanix-manifest.yml

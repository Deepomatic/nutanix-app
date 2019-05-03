#!/bin/bash

set -e

ROOT=$(dirname $0)

export DOCKER_IMAGE_NAME=deepomatic/nutanix-runtime:master-22
export DEPLOYMENT_NAME=deepomatic-app
export NEURAL_WORKER_VERSION=deepomatic/vulcan-worker-nn-on-premises-rc:master-495-combo
export RESOURCE_SERVER_VERSION=deepomatic/resource-server-on-premises-rc:master2-7
export DEEPOMATIC_SITE_ID=${NUTANIX_RUNTIME_SITE_ID}
export IMAGE_PULL_SECRETS=""
export NATS_SERVICE=""

eval "cat <<EOF
$(<${ROOT}/../deploy/k8s-manifest.yml)
EOF
" 2> /dev/null > ${ROOT}/nutanix-manifest.yml

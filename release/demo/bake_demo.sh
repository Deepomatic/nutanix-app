#!/bin/bash

set -e

DEMO_IMAGE_NAME=deepomatic/nutanix-app-demo:0.1.0-gesture
EXPORT_DIR=`pwd`/$(dirname $0)/app_export
source $(dirname $0)/../common.sh

echo "Exporting resources to ${EXPORT_DIR}"

CID=$(docker run --rm -d \
    -v ${EXPORT_DIR}:/app \
    -e DOWNLOAD_ON_STARTUP=1 \
    -e INIT_SYSTEM=circus \
    -e DEEPOMATIC_APP_ID=${NUTANIX_RUNTIME_APP_ID} \
    -e DEEPOMATIC_API_KEY=${NUTANIX_RUNTIME_API_KEY} \
    -e DEEPOMATIC_SITE_ID=${NUTANIX_RUNTIME_SITE_ID} \
    ${RESOURCE_SERVER_VERSION})

while [ ! `docker exec ${CID} ls /tmp/resource-server-ready` ]; do
    echo "not ready"
done

docker build -t ${DEMO_IMAGE_NAME} --build-arg ROOT=${NEURAL_WORKER_VERSION} .

docker push ${DEMO_IMAGE_NAME}

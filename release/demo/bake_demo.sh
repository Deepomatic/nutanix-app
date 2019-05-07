#!/bin/bash

set -e

DEMO_IMAGE_NAME=${DEMO_IMAGE_NAME:-deepomatic/nutanix-app-demo:0.1.0-gesture}
echo "Docker image ${DEMO_IMAGE_NAME}"

ROOT=`pwd`/$(dirname $0)
EXPORT_DIR=${ROOT}/app_export
source ${ROOT}/../scripts/common.sh

echo "Exporting resources to ${EXPORT_DIR}"
rm -rf ${EXPORT_DIR}

CMD="docker run --rm -d \
    -v ${EXPORT_DIR}:/app \
    -e DOWNLOAD_ON_STARTUP=1 \
    -e INIT_SYSTEM=circus \
    -e DEEPOMATIC_APP_ID=${NUTANIX_RUNTIME_APP_ID} \
    -e DEEPOMATIC_API_KEY=${NUTANIX_RUNTIME_API_KEY} \
    -e DEEPOMATIC_SITE_ID=${NUTANIX_RUNTIME_SITE_ID} \
    ${RESOURCE_SERVER_VERSION}"
echo "Runing $CMD"
CID=$($CMD)

DONE="0"
while [ "$DONE" = "0" ]; do
    DONE=$(docker logs $CID 2>&1 | grep "Sending start to service worker-nn" | wc -l | sed "s/ *//g")
    sleep 1
    echo "Waiting until download resource complete"
done
docker stop $CID

docker build -t ${DEMO_IMAGE_NAME} --build-arg ROOT=${NEURAL_WORKER_VERSION} .

docker push ${DEMO_IMAGE_NAME}

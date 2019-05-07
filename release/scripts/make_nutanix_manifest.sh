#!/bin/bash

set -e

source $(dirname $0)/common.sh

export DEPLOYMENT_NAME=$1
TEMPLATE=$2
OUTPUT=$3

eval "cat <<EOF
$(<${TEMPLATE})
EOF
" 2> /dev/null > $OUTPUT

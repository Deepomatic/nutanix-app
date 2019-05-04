#!/bin/bash

set -e

source $(dirname $0)/common.sh

TEMPLATE=$1
OUTPUT=$2

eval "cat <<EOF
$(<${TEMPLATE})
EOF
" 2> /dev/null > $OUTPUT

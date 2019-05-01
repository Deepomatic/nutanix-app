#!/bin/bash

apt update
apt install -y --no-install-recommends protobuf-compiler

pip3 install -r $(dirname $0)/requirements.txt

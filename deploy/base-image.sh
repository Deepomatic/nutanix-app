#!/bin/bash

apt update
apt install -y --no-install-recommends protobuf-compiler

pip3 install -r deploy/requirements.txt

#!/usr/bin/env bash

set -euo pipefail

# install python 3.10
apt-get update -y
apt-get install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get install -y python3.10 python3.10-distutils

# clean apt cache; this keeps the image small
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# install aga
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10
pip install wheel
python3.10 -m pip cache purge

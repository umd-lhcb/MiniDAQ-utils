#!/bin/bash

echo "This installation only supports CentOS!"

sudo yum install python3-devel dim-devel gcc

export CPLUS_INCLUDE_PATH=/usr/local/include/dim
pip3 install pydim "$@"

pip3 install -r ../requirements.txt "$@"

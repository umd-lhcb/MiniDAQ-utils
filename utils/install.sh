#!/bin/bash

echo "This installation only supports CentOS!"

sudo yum install python3-devel dim-devel gcc

export CPLUS_INCLUDE_PATH=/usr/local/include/dim
pip install pydim "$@"

pip install -r ../requirements.txt "$@"

#!/bin/bash

#NetProbes startiup script

CUR_DIR=$(pwd)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pymain=$DIR"/app/probe/main.py"
py=$(which python3)

exec $py $pymain "$@"


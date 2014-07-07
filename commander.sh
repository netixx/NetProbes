#!/bin/bash

#commander startiup script

CUR_DIR=$(pwd)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
pymain=$DIR"/app/commander/main.py"
py=$(which python3)

#TODO: read id from cmdline
#TODO: read commander from command line
$py "$pymain" "$@"


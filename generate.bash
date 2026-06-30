#!/usr/bin/env bash
set -e

SCRIPT_PATH="${BASH_SOURCE[0]}"

CURRENT_PATH=$(dirname $SCRIPT_PATH)
cd $CURRENT_PATH/fussel

source .venv/bin/activate
# Generate site
./fussel.py


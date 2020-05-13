#!/usr/bin/env bash
set -e

SCRIPT_PATH="${BASH_SOURCE[0]}"

CURRENT_PATH=$(dirname $SCRIPT_PATH)
cd $CURRENT_PATH

# Generate site
./fussel.py

# Rebuild node site
pushd web
yarn build
popd

printf "Site generated at: ${CURRENT_PATH}/web/build"
printf "\n\n To validate build run: \n   python -m http.server --directory web/build\n\n"



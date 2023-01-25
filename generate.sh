#!/usr/bin/env bash
set -e

SCRIPT_PATH="${BASH_SOURCE[0]}"

CURRENT_PATH=$(dirname $SCRIPT_PATH)
cd $CURRENT_PATH/fussel

# Generate site
./fussel.py

# Rebuild node site
pushd web
yarn build
popd

printf "Site generated at: ${CURRENT_PATH}/fussel/web/build"
printf "\n\n To validate build run: \n   /usr/bin/env python3 -m http.server --directory fussel/web/build\n\n"



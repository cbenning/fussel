#!/usr/bin/env bash

pushd fussel

echo "Generating yaml config..."
curl --silent -XGET --unix-socket /run/docker.sock http://localhost/containers/${HOSTNAME}/json | jq '.Config.Labels' > flat_config.json
utils/./flat_json_to_nested_json.py flat_config.json > config.json
yq -P config.json > config.yml
cat config.yml

./generate.sh

_PUID=$(id -u)
_PGID=$(id -g)
DO_CHOWN=0
if [[ ! -z "${PUID}" ]]; then
 _PUID=${PUID}
 DO_CHOWN=1
fi
if [[ ! -z "${PGID}" ]]; then
 _PGID=${PGID}
 DO_CHOWN=1
fi
if (( DO_CHOWN > 0 )); then
 echo "Fixing permissions..."
 OUTPUT_PATH=$(cat config.yml | yq '.gallery.output_path')
 chown -R ${_PUID}:${_PGID} ${OUTPUT_PATH}
fi

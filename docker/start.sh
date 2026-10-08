#!/usr/bin/env bash

pushd fussel

set -e 

source .venv/bin/activate

echo "Generating yaml config..."

../generate_config.sh ../template_config.yml > config.yml

cat config.yml

python -m fussel.fussel


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
 echo "Fixing output directory permissions..."
 chown -R ${_PUID}:${_PGID} ${OUTPUT_PATH}
fi

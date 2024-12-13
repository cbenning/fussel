#!/usr/bin/env bash

pushd fussel

set -e 

source fussel/.venv/bin/activate

echo "Generating yaml config..."

jinja2 \
    -D INPUT_PATH="\"${INPUT_PATH}\"" \
    -D OUTPUT_PATH="\"${OUTPUT_PATH}\"" \
    -D OVERWRITE="${OVERWRITE}" \
    -D EXIF_TRANSPOSE="${EXIF_TRANSPOSE}" \
    -D RECURSIVE="${RECURSIVE}" \
    -D RECURSIVE_NAME_PATTERN="\"${RECURSIVE_NAME_PATTERN}\"" \
    -D FACE_TAG_ENABLE="${FACE_TAG_ENABLE}" \
    -D WATERMARK_ENABLE="${WATERMARK_ENABLE}" \
    -D WATERMARK_PATH="\"${WATERMARK_PATH}\"" \
    -D WATERMARK_SIZE_RATIO="${WATERMARK_SIZE_RATIO}" \
    -D SITE_ROOT="\"${SITE_ROOT}\"" \
    -D SITE_TITLE="\"${SITE_TITLE}\"" \
    ../template_config.yml > config.yml

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
 echo "Fixing output directory permissions..."
 chown -R ${_PUID}:${_PGID} ${OUTPUT_PATH}
fi

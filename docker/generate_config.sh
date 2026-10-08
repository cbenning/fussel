#!/usr/bin/env bash
# Render a config.yml from the environment variables, using the given template.
# Usage: generate_config.sh <template> > config.yml
#
# Values are passed through raw. The template quotes and escapes string values itself (the q macro),
# and leaves booleans and numbers unquoted so they keep their YAML type.
set -e

jinja2 \
    -D INPUT_PATH="${INPUT_PATH}" \
    -D OUTPUT_PATH="${OUTPUT_PATH}" \
    -D OVERWRITE="${OVERWRITE}" \
    -D EXIF_TRANSPOSE="${EXIF_TRANSPOSE}" \
    -D ALLOW_DOWNLOAD="${ALLOW_DOWNLOAD}" \
    -D RECURSIVE="${RECURSIVE}" \
    -D RECURSIVE_NAME_PATTERN="${RECURSIVE_NAME_PATTERN}" \
    -D FACE_TAG_ENABLE="${FACE_TAG_ENABLE}" \
    -D WATERMARK_ENABLE="${WATERMARK_ENABLE}" \
    -D WATERMARK_PATH="${WATERMARK_PATH}" \
    -D WATERMARK_SIZE_RATIO="${WATERMARK_SIZE_RATIO}" \
    -D SITE_ROOT="${SITE_ROOT}" \
    -D SITE_TITLE="${SITE_TITLE}" \
    -D PARALLEL_TASKS="${PARALLEL_TASKS}" \
    "$1" < /dev/null

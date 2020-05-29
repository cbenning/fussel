#!/usr/bin/env bash


pushd fussel

export INPUT_PATH=/input
export OUTPUT_PATH=web/build

FAILED=0

echo "" > .env

while IFS= read -r line
do
  CONF_VAL_REGEX='^([A-Z_]+)=(.*)$'
  if [[ $line =~ $CONF_VAL_REGEX ]]; then
    CONF_VAR="${BASH_REMATCH[1]}"
    if [[ ! -z "${!CONF_VAR}" ]]; then
      echo "${CONF_VAR}=${!CONF_VAR}" >> .env
    else
      echo "${CONF_VAR}=${BASH_REMATCH[2]}" >> .env
    fi
  fi

  REQ_CONF_VAL_REGEX='^#([A-Z_]+)=.*$'
  if [[ $line =~ $REQ_CONF_VAL_REGEX ]]; then
    REQ_CONF_VAR="${BASH_REMATCH[1]}"
    if [[ ! -z "${!REQ_CONF_VAR}" ]]; then
      echo "${REQ_CONF_VAR}=${!REQ_CONF_VAR}" >> .env
    else
      echo "Missing required config:"
      echo "${REQ_CONF_VAR}"
      FAILED=1
    fi
  fi

done < ".env.sample"

if (( FAILED > 0 )); then
  exit 1
fi

echo "Using config: "
cat .env

./generate_site.sh

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
  chown -R ${_PUID}:${_PGID} ${OUTPUT_PATH}
fi

echo "\nExtra docker instructions:"
echo " To validate build run:"
echo "   python -m http.server --directory <your-output-mapping>"

popd


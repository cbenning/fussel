#!/usr/bin/env bash
# Install a built wheel into a clean environment and generate a tiny gallery with it.
# Fails if the prebuilt web app or the gallery data is missing from the result.
#
# Usage: scripts/smoke_test_wheel.sh dist/fussel-<version>-py3-none-any.whl
set -euo pipefail

WHEEL="$(realpath "${1:?usage: $0 path/to/fussel.whl}")"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$WORK/photos/Trip"
# Create the sample photo with the wheel's own dependencies (Pillow)
uv run --no-project --isolated --with "$WHEEL" python -c \
  "from PIL import Image; Image.new('RGB', (1600, 1000), 'teal').save('$WORK/photos/Trip/one.jpg')"

cat > "$WORK/config.yml" <<YAML
gallery:
  input_path: "$WORK/photos"
  output_path: "$WORK/site"
  parallel_tasks: 1
  people:
    enable: False
site:
  title: "Smoke Test"
  http_root: "/"
YAML

# Run from an unrelated directory to prove nothing depends on a checkout
(cd "$WORK" && uv run --no-project --isolated --with "$WHEEL" fussel --config config.yml)

for f in index.html static/_gallery/data/site.json static/_gallery/data/albums.json \
         static/_gallery/data/people.json static/_gallery/data/photos.json; do
  [ -s "$WORK/site/$f" ] || { echo "smoke test failed: missing $f" >&2; exit 1; }
done
ls "$WORK/site/assets"/*.js > /dev/null || { echo "smoke test failed: no web app bundle" >&2; exit 1; }
grep -q '"Trip"' "$WORK/site/static/_gallery/data/albums.json" \
  || { echo "smoke test failed: album missing from albums.json" >&2; exit 1; }

echo "smoke test passed: $WHEEL"

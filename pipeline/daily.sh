#!/bin/bash
# God mode per channel: trending topic -> short with Pexels visuals -> upload.
# Usage: ./pipeline/daily.sh <channel-name> [public|unlisted|private]
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
channel=$1

topic=$($PY pipeline/trend_picker.py "$channel")
echo "[daily/$channel] topic: $topic"
$PY pipeline/make_short.py "$topic"
slug=$(echo "$topic" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]\+/-/g;s/^-//;s/-$//' | cut -c1-60)
$PY pipeline/yt_upload.py "workspace/$slug" "${2:-private}" "$channel"

# IG cross-post only for channels that opt in via config.json ig_account
ig=$($PY -c "import json;print(json.load(open('channels/$channel/config.json')).get('ig_account',''))")
if [ -n "$ig" ]; then
  $PY pipeline/ig_upload.py "workspace/$slug" || echo "[daily/$channel] IG publish FAILED (YT already up)"
fi

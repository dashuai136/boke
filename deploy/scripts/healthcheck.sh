#!/usr/bin/env bash
set -euo pipefail

URL="${1:-http://127.0.0.1:8080/api/species?page_size=1}"

code=$(curl -s -o /tmp/begonia_health.json -w "%{http_code}" "$URL")
if [[ "$code" != "200" ]]; then
  echo "[FAIL] healthcheck status=$code url=$URL"
  exit 1
fi

echo "[OK] healthcheck status=200 url=$URL"
head -c 200 /tmp/begonia_health.json; echo

#!/usr/bin/env bash
# Check whether ComfyUI is reachable.
#
# Exit codes:
#   0  ComfyUI is online (HTTP 200 from the root path)
#   1  ComfyUI did NOT respond (offline, unreachable, or timeout)
#
# Configuration:
#   COMFYUI_URL  – override the URL to probe (default: http://localhost:6677)
#
# Usage:
#   bash scripts/check_comfyui.sh
#   COMFYUI_URL=http://192.168.1.10:6677 bash scripts/check_comfyui.sh

set -u

URL="${COMFYUI_URL:-http://localhost:6677}"

code="$(curl -s -m 5 -o /dev/null -w '%{http_code}' "${URL}/" || true)"

if [[ "${code}" == "200" ]]; then
  echo "ComfyUI ONLINE  (${URL}, HTTP ${code})"
  exit 0
fi

echo "ComfyUI OFFLINE (${URL}, HTTP ${code:-no-response})" >&2
echo "  - Start ComfyUI locally and retry, OR" >&2
echo "  - Fall back to Hermes' built-in image_generate tool (no API key needed)." >&2
exit 1

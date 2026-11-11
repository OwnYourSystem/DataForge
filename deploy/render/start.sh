#!/usr/bin/env bash
# Starts the API (private, on localhost) and the web server (public).
# If one of them stops, the script stops, and the host restarts the container.
set -euo pipefail

(cd /srv/apps/api && exec uvicorn dataforge.main:app_factory --factory --host 127.0.0.1 --port 8000) &
(cd /srv/web && PORT="${PORT:-3000}" exec node server.js) &

wait -n
echo "a process stopped; stopping the container" >&2
exit 1

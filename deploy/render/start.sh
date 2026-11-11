#!/usr/bin/env bash
# Starts the API (private, on localhost) and the web server (public), and
# the worker when DF_RUN_WORKER=1.
# If one of them stops, the script stops, and the host restarts the container.
set -euo pipefail

(cd /srv/apps/api && exec uvicorn dataforge.main:app_factory --factory --host 127.0.0.1 --port 8000) &
(cd /srv/web && PORT="${PORT:-3000}" exec node server.js) &
if [ "${DF_RUN_WORKER:-0}" = "1" ]; then
  # Single-container mode: the worker runs here too. See the Dockerfile.
  # The API creates the database tables at startup. Wait for it, so that the
  # two processes do not create the tables at the same time.
  (
    for _ in $(seq 1 60); do
      python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/healthz', timeout=2)" \
        2>/dev/null && break
      sleep 1
    done
    cd /srv/apps/api && exec python -m dataforge.worker
  ) &
fi

wait -n
echo "a process stopped; stopping the container" >&2
exit 1

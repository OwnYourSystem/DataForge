#!/usr/bin/env bash
# Smoke test against a running stack: save the reference solution, run it,
# and require a pass. Usage: scripts/smoke.sh [api-url]
set -euo pipefail
API="${1:-http://localhost:8000}"
USER_HEADER="X-Dev-User: smoke-$RANDOM"
MODEL="models/staging/stg_customers.sql"
SOLUTION="$(dirname "$0")/../curriculum/retail-lakehouse/lab-001/solution/$MODEL"

json() { python3 -c "import json,sys; print(json.load(sys.stdin)$1)"; }
call() { curl -fsS -H "$USER_HEADER" -H "Content-Type: application/json" "$@"; }

project=$(call -X POST "$API/v1/projects" -d '{"lesson_id":"lab-001"}' | json "['id']")
python3 -c "import json,sys; print(json.dumps({'content': open(sys.argv[1]).read()}))" "$SOLUTION" \
  | call -X PUT "$API/v1/projects/$project/files/$MODEL" -d @- > /dev/null
execution=$(call -X POST "$API/v1/projects/$project/executions" -d '{"operation_id":"dbt_build"}' | json "['id']")

for _ in $(seq 1 90); do
  status=$(call "$API/v1/executions/$execution" | json "['status']")
  case "$status" in queued|running) sleep 1 ;; *) break ;; esac
done

result=$(call "$API/v1/executions/$execution")
echo "status: $status"
echo "$result" | json "['assessment']"
[ "$(echo "$result" | json "['assessment']['passed']")" = "True" ] || { echo "$result" | json "['logs']"; exit 1; }
echo "smoke test passed"

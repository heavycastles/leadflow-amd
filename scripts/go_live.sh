#!/usr/bin/env bash
# One-command AMD Token Factory live path.
# Usage:
#   ./scripts/go_live.sh rc-YOUR_KEY          # write .env + verify (python -m app.llm)
#   AMD_TOKEN_FACTORY_API_KEY=rc-... ./scripts/go_live.sh
#   ./scripts/go_live.sh rc-YOUR_KEY --demo   # also start serve.py and run scripts/demo.sh
#   ./scripts/go_live.sh --check              # verify only (key already in .env / env)
#
# Never prints the key. Does not push, deploy, or submit.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DO_DEMO=0
DO_CHECK_ONLY=0
KEY=""
for arg in "$@"; do
  case "$arg" in
    --demo) DO_DEMO=1 ;;
    --check) DO_CHECK_ONLY=1 ;;
    -h|--help)
      sed -n '2,10p' "$0"
      exit 0
      ;;
    rc-*|sk-*) KEY="$arg" ;;
    *)
      if [[ -z "$KEY" && "$arg" != --* ]]; then KEY="$arg"; fi
      ;;
  esac
done

if [[ -z "$KEY" ]]; then
  KEY="${AMD_TOKEN_FACTORY_API_KEY:-${RADEON_API_KEY:-}}"
fi

PY="${ROOT}/.venv/bin/python"
[[ -x "$PY" ]] || PY="$(command -v python3)"

write_env_key() {
  local k="$1"
  if [[ ! -f .env ]]; then
    if [[ -f .env.example ]]; then
      cp .env.example .env
      echo "  created .env from .env.example"
    else
      touch .env
      echo "  created empty .env"
    fi
  fi
  # Upsert AMD_TOKEN_FACTORY_API_KEY=... without echoing the value
  if grep -qE '^[[:space:]]*AMD_TOKEN_FACTORY_API_KEY=' .env 2>/dev/null; then
    # portable in-place replace (no GNU sed -i assumed beyond basic)
    local tmp
    tmp="$(mktemp)"
    awk -v k="$k" '
      BEGIN { done=0 }
      /^[[:space:]]*AMD_TOKEN_FACTORY_API_KEY=/ {
        print "AMD_TOKEN_FACTORY_API_KEY=" k
        done=1
        next
      }
      { print }
      END { if (!done) print "AMD_TOKEN_FACTORY_API_KEY=" k }
    ' .env > "$tmp"
    mv "$tmp" .env
    echo "  updated AMD_TOKEN_FACTORY_API_KEY in .env"
  else
    printf '\nAMD_TOKEN_FACTORY_API_KEY=%s\n' "$k" >> .env
    echo "  appended AMD_TOKEN_FACTORY_API_KEY to .env"
  fi
  # Ensure .env stays ignored
  if ! git check-ignore -q .env 2>/dev/null; then
    echo "WARNING: .env may not be gitignored — check .gitignore before any commit" >&2
  fi
}

if [[ "$DO_CHECK_ONLY" -eq 0 ]]; then
  if [[ -z "$KEY" ]]; then
    echo "ERROR: pass the Token Factory key as arg, or set AMD_TOKEN_FACTORY_API_KEY / RADEON_API_KEY" >&2
    echo "  Get a key (no card): https://notebooks.amd.com/tokenfactory" >&2
    echo "  Example: ./scripts/go_live.sh rc-..." >&2
    exit 1
  fi
  echo "== go_live: write key + verify =="
  write_env_key "$KEY"
else
  echo "== go_live: verify only =="
fi

# Load .env into this shell for the check (serve.py also loads it)
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

echo "  running: $PY -m app.llm"
CHECK_JSON="$("$PY" -m app.llm)" || {
  echo "ERROR: live check crashed. Fix and re-run." >&2
  exit 1
}
echo "$CHECK_JSON"
OK_FLAG="$(printf '%s' "$CHECK_JSON" | "$PY" -c 'import json,sys; print("1" if json.load(sys.stdin).get("ok") else "0")')"
if [[ "$OK_FLAG" != "1" ]]; then
  echo "ERROR: live check failed (ok=false) — key missing/rejected or network issue." >&2
  exit 1
fi
echo "  OK live check (ok=true)"

if [[ "$DO_DEMO" -eq 1 ]]; then
  echo "== go_live: start serve.py + demo =="
  # Kill previous local serve on 8080 if we started one (best-effort)
  if curl -sf -o /dev/null --max-time 1 http://127.0.0.1:8080/metrics 2>/dev/null; then
    echo "  serve already responding on :8080 — reusing"
  else
    "$PY" serve.py &
    SERVE_PID=$!
    trap 'kill "$SERVE_PID" 2>/dev/null || true' EXIT
    for i in $(seq 1 30); do
      if curl -sf -o /dev/null --max-time 1 http://127.0.0.1:8080/metrics 2>/dev/null; then
        break
      fi
      sleep 0.3
    done
    if ! curl -sf -o /dev/null --max-time 1 http://127.0.0.1:8080/metrics 2>/dev/null; then
      echo "ERROR: serve.py did not become ready on :8080" >&2
      exit 1
    fi
    echo "  serve.py ready (pid $SERVE_PID)"
  fi
  bash scripts/demo.sh http://127.0.0.1:8080
fi

echo "Done. Dashboard: python serve.py  →  http://127.0.0.1:8080"
echo "Re-check anytime: ./scripts/go_live.sh --check"

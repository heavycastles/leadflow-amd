#!/usr/bin/env bash
# Local ship checklist for AMD ACT III LeadFlow — no secrets, no push/submit.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
fail=0

ok() { printf '  OK  %s\n' "$1"; }
bad() { printf ' FAIL %s\n' "$1"; fail=1; }

echo "== LeadFlow preflight (local only) =="

# 1) Tests
if [[ -x .venv/bin/pytest ]]; then
  PYTEST=(.venv/bin/pytest)
elif command -v pytest >/dev/null 2>&1; then
  PYTEST=(pytest)
else
  bad "pytest not found (activate .venv or install requirements-dev.txt)"
  PYTEST=()
fi
if ((${#PYTEST[@]})); then
  if "${PYTEST[@]}" -q; then
    ok "pytest passed"
  else
    bad "pytest failed"
  fi
fi

# 2) No .env staged / tracked
if [[ -f .env ]]; then
  if git check-ignore -q .env 2>/dev/null || grep -qxF '.env' .gitignore 2>/dev/null; then
    ok ".env present but gitignored"
  else
    bad ".env exists and may not be ignored"
  fi
else
  ok "no .env file"
fi
if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  bad ".env is tracked by git — unstage/remove before ship"
elif git diff --cached --name-only 2>/dev/null | grep -qxF '.env'; then
  bad ".env is staged — unstage before ship"
else
  ok ".env not staged/tracked"
fi

# 3) Required files
[[ -f LICENSE ]] && ok "LICENSE present" || bad "LICENSE missing"
[[ -f render.yaml ]] && ok "render.yaml present" || bad "render.yaml missing"
[[ -f Dockerfile ]] && ok "Dockerfile present" || bad "Dockerfile missing"
[[ -f docker-compose.yml ]] && ok "docker-compose.yml present" || bad "docker-compose.yml missing"
[[ -f serve.py ]] && ok "serve.py present" || bad "serve.py missing"
[[ -f .github/workflows/ci.yml ]] && ok "CI workflow present" || bad ".github/workflows/ci.yml missing"
[[ -f docs/benchmarks-mock.md ]] && ok "docs/benchmarks-mock.md present" || bad "docs/benchmarks-mock.md missing"

# 4) Demo video
if [[ -f docs/demo-v3.mp4 ]]; then
  ok "docs/demo-v3.mp4 exists"
elif [[ -f docs/demo-v2.mp4 ]]; then
  ok "docs/demo-v2.mp4 exists (prefer demo-v3.mp4)"
elif [[ -f docs/demo-draft.mp4 ]]; then
  ok "docs/demo-draft.mp4 exists (prefer demo-v3.mp4)"
else
  bad "no docs/demo-*.mp4 found"
fi

echo
echo "== Remaining USER checklist (from SUBMISSION.md) =="
if [[ -f SUBMISSION.md ]]; then
  # Print the numbered list under "**Remaining before submit (user):**"
  awk '
    /^\*\*Remaining before submit \(user\):\*\*/ {p=1; next}
    p && /^[0-9]+\./ {print; next}
    p && NF==0 {next}
    p && !/^[0-9]+\./ {exit}
  ' SUBMISSION.md || true
else
  echo "(SUBMISSION.md missing)"
fi

echo
if ((fail)); then
  echo "Preflight FAILED — fix items above before ship."
  exit 1
fi
echo "Preflight PASSED (local). Do not push/submit until USER steps are done."
exit 0

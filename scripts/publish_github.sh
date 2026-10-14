#!/usr/bin/env bash
# Creates public repo heavycastles/leadflow-amd and pushes main.
# Requires: gh authenticated as heavycastles. Do NOT run until ready.
set -euo pipefail
cd "$(dirname "$0")/.."

REPO_NAME="leadflow-amd"
OWNER="heavycastles"
REMOTE_URL="https://github.com/${OWNER}/${REPO_NAME}.git"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "gh is not logged in — authenticate as ${OWNER} first" >&2
  exit 1
fi

# Local pack sanity (no push yet)
if [[ ! -f .github/workflows/ci.yml ]]; then
  echo "missing .github/workflows/ci.yml — add CI before publishing" >&2
  exit 1
fi
if [[ -n "$(git status --porcelain)" ]]; then
  echo "working tree dirty — commit or stash before publishing" >&2
  exit 1
fi
if [[ -x ./scripts/preflight_submit.sh ]]; then
  ./scripts/preflight_submit.sh || { echo "preflight failed — fix before publishing" >&2; exit 1; }
fi

LOGIN=$(gh api user -q .login)
if [[ "$LOGIN" != "$OWNER" ]]; then
  echo "gh logged in as '${LOGIN}', expected '${OWNER}'" >&2
  exit 1
fi

if gh repo view "${OWNER}/${REPO_NAME}" >/dev/null 2>&1; then
  echo "Repo ${OWNER}/${REPO_NAME} already exists — adding remote and pushing"
else
  gh repo create "${OWNER}/${REPO_NAME}" --public --source=. --remote=origin --description "LeadFlow AI — multilingual commerce lead & order agent on AMD MI300X (ACT III)"
fi

git branch -M main 2>/dev/null || true
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE_URL"
else
  git remote add origin "$REMOTE_URL"
fi

git push -u origin main
echo "Published: https://github.com/${OWNER}/${REPO_NAME}"

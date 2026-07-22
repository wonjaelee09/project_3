#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

TOKEN_FILE="GITHUB_TOKEN.env"
if [[ ! -f "$TOKEN_FILE" && -f ".env" ]]; then
  TOKEN_FILE=".env"
fi

if [[ ! -f "$TOKEN_FILE" ]]; then
  echo "Missing token file. Create .env or GITHUB_TOKEN.env and set GITHUB_TOKEN." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$TOKEN_FILE"
set +a

if [[ -z "${GITHUB_TOKEN:-}" || "${GITHUB_TOKEN}" == "paste_token_here" ]]; then
  echo "GITHUB_TOKEN is empty or still set to placeholder in .env" >&2
  exit 1
fi

original_url="$(git remote get-url origin)"
cleanup() {
  git remote set-url origin "$original_url" >/dev/null 2>&1 || true
}
trap cleanup EXIT

auth_prefix="https://x-access-token:${GITHUB_TOKEN}"
auth_host="github.com/wonjaelee09/project_3.git"
git remote set-url origin "${auth_prefix}@${auth_host}"
git push origin master

echo "Push complete. Remote URL restored to: $original_url"

#!/bin/sh
# Reproduce the full pipeline from a clean clone in a temp directory.
set -eux
PS4='> '

repo_url="${1:?Usage: $0 <repo-url-or-path>}"

cd "$(mktemp -d "${TMPDIR:-/tmp}/stellar-XXXXXXX")"
echo "Working in: $(pwd)"

git clone "$repo_url" stellar-distance
cd stellar-distance

python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

make clean
make
make test

echo "=== PASSED: reproduced from scratch ==="

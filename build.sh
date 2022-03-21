#!/usr/bin/env bash

set -eo pipefail

echo "==> Changing directory"
cd "$(dirname "$0")"

echo "==> Building project"
python3 -m build
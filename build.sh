#!/usr/bin/env bash

set -eo pipefail

echo "==> Writing version file"
echo "VERSION = \"$VERSION\"" > kasushi/_version_data.py

echo "==> Changing directory"
cd "$(dirname "$0")"

echo "==> Building project"
python3 -m build
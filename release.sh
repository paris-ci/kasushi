#!/usr/bin/env bash

export COLOR_NC='\033[0m' # No Color
export COLOR_RED='\033[0;31m'

set -eo pipefail

echo "==> Changing directory"
cd "$(dirname "$0")"

PREVIOUS_GIT_TAG=$(git describe --abbrev=0 --tags)


# Ensure working tree is clean or ask to commit
# Don't continue while working tree isn't clean

while true; do
  if [[ -n $(git status --porcelain) ]]; then
    echo "==> ! Working tree is not clean. Please commit or stash changes before releasing. Press enter when done."
    # Wait for key press
    read -r
  else
    break
  fi
done

echo -e "==> Previous version was v$COLOR_RED$PREVIOUS_GIT_TAG$COLOR_NC"

# Ask for input
echo "==> ! Enter the new version number (e.g. 1.2.3)> "
read -r NEW_GIT_TAG

# Create tag for new release
git tag "$NEW_GIT_TAG"
echo "==> Created tag $NEW_GIT_TAG"

# Push tag to github
git push origin "$NEW_GIT_TAG"
echo "==> Pushed tag $NEW_GIT_TAG"

# Run build script
echo "==> Running build script"
./build.sh
twine check dist/*

twine upload dist/*

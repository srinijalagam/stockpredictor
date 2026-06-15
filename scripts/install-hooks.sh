#!/usr/bin/env bash
# Install the project git hooks into .git/hooks (no git config changes).
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
src="$repo_root/.githooks"
dst="$repo_root/.git/hooks"

mkdir -p "$dst"
for hook in "$src"/*; do
  name="$(basename "$hook")"
  cp "$hook" "$dst/$name"
  chmod +x "$dst/$name"
  echo "Installed $name -> .git/hooks/$name"
done
echo "Done. Git hooks are active."

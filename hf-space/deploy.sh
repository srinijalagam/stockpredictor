#!/usr/bin/env bash
# Deploy the Stock Predictor to a Hugging Face Docker Space (Linux/macOS/WSL).
#
# Prerequisites:
#   1. A Hugging Face account and a WRITE token: https://huggingface.co/settings/tokens
#   2. git installed.
#
# Usage:
#   export HF_TOKEN=hf_xxx
#   ./hf-space/deploy.sh your-username/stock-predictor
#
# The Space is created automatically on first push. After the first deploy, set
# OPENAI_API_KEY (and friends) as Space secrets: Settings -> Variables and secrets.
set -euo pipefail

SPACE="${1:-}"
TOKEN="${HF_TOKEN:-}"

if [[ -z "$SPACE" ]]; then
  echo "Usage: $0 <username/space-name>   (with HF_TOKEN exported)" >&2
  exit 1
fi
if [[ -z "$TOKEN" ]]; then
  echo "No token. Export HF_TOKEN with a Hugging Face WRITE token." >&2
  exit 1
fi

HF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HF_DIR")"
BUILD="$HF_DIR/build"

echo "Assembling Space tree in $BUILD ..."
rm -rf "$BUILD"
mkdir -p "$BUILD/agent" "$BUILD/ui"

cp "$HF_DIR/Dockerfile" "$HF_DIR/README.md" "$HF_DIR/serve.py" "$BUILD/"

cp "$ROOT/agent/requirements.txt" "$BUILD/agent/"
cp -r "$ROOT/agent/app" "$BUILD/agent/app"

for f in package.json tsconfig.json vite.config.ts index.html; do
  cp "$ROOT/ui/$f" "$BUILD/ui/"
done
cp -r "$ROOT/ui/src" "$BUILD/ui/src"

cat > "$BUILD/.gitignore" <<'EOF'
.env
.env.*
node_modules/
dist/
__pycache__/
*.pyc
EOF

echo "Pushing to https://huggingface.co/spaces/$SPACE ..."
cd "$BUILD"
git init -q
git checkout -q -B main
git add -A
git -c user.email="deploy@local" -c user.name="hf-deploy" commit -q -m "Deploy Stock Predictor"
git push -f "https://user:${TOKEN}@huggingface.co/spaces/${SPACE}" main

echo ""
echo "Done. Building at: https://huggingface.co/spaces/$SPACE"
echo "Next: set OPENAI_API_KEY (+ OPENAI_BASE_URL, OPENAI_MODEL) as Space secrets."

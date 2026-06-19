# Deploy the Stock Predictor to a Hugging Face Docker Space (Windows PowerShell).
#
# Prerequisites:
#   1. A Hugging Face account and a WRITE access token:
#      https://huggingface.co/settings/tokens
#   2. git installed.
#
# Usage:
#   $env:HF_TOKEN = "hf_xxx"
#   ./hf-space/deploy.ps1 -Space "your-username/stock-predictor"
#
# The Space is created automatically on first push if it doesn't exist.
# After the first deploy, set OPENAI_API_KEY (and friends) as Space secrets in
# the UI: Settings -> Variables and secrets. Do NOT commit your .env.

param(
  [Parameter(Mandatory = $true)] [string] $Space,
  [string] $Token = $env:HF_TOKEN
)

$ErrorActionPreference = "Stop"

if (-not $Token) {
  throw "No token. Set `$env:HF_TOKEN to a Hugging Face WRITE token, or pass -Token."
}

$hf    = $PSScriptRoot
$root  = Split-Path -Parent $hf
$build = Join-Path $hf "build"

Write-Host "Assembling Space tree in $build ..."
if (Test-Path $build) { Remove-Item -Recurse -Force $build }
New-Item -ItemType Directory -Path $build | Out-Null

# HF-specific files (Dockerfile, README front matter, entrypoint).
Copy-Item (Join-Path $hf "Dockerfile") $build
Copy-Item (Join-Path $hf "README.md")  $build
Copy-Item (Join-Path $hf "serve.py")   $build

# Agent source (no caches / venvs).
$agentDst = Join-Path $build "agent"
New-Item -ItemType Directory -Path $agentDst | Out-Null
Copy-Item (Join-Path $root "agent\requirements.txt") $agentDst
Copy-Item -Recurse (Join-Path $root "agent\app") (Join-Path $agentDst "app")

# UI source only (node_modules / dist are rebuilt inside the Docker image).
$uiDst = Join-Path $build "ui"
New-Item -ItemType Directory -Path $uiDst | Out-Null
foreach ($f in @("package.json", "tsconfig.json", "vite.config.ts", "index.html")) {
  Copy-Item (Join-Path $root "ui\$f") $uiDst
}
Copy-Item -Recurse (Join-Path $root "ui\src") (Join-Path $uiDst "src")

# Space-local .gitignore so we never push secrets or build junk.
@"
.env
.env.*
node_modules/
dist/
__pycache__/
*.pyc
"@ | Set-Content -Path (Join-Path $build ".gitignore") -Encoding utf8

Write-Host "Pushing to https://huggingface.co/spaces/$Space ..."
Push-Location $build
try {
  git init -q
  git checkout -q -B main
  git add -A
  git -c user.email="deploy@local" -c user.name="hf-deploy" commit -q -m "Deploy Stock Predictor"
  $remote = "https://user:$Token@huggingface.co/spaces/$Space"
  git push -f $remote main
}
finally {
  Pop-Location
}

Write-Host ""
Write-Host "Done. Building at: https://huggingface.co/spaces/$Space"
Write-Host "Next: set OPENAI_API_KEY (+ OPENAI_BASE_URL, OPENAI_MODEL) as Space secrets."

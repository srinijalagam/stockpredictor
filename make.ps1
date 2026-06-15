<#
.SYNOPSIS
  Windows/PowerShell equivalent of the Makefile for the Stock Predictor stack.

.EXAMPLE
  ./make.ps1 env
  ./make.ps1 build
  ./make.ps1 package
  ./make.ps1 up
  ./make.ps1 logs
  ./make.ps1 clean
#>
param(
  [Parameter(Position = 0)]
  [ValidateSet('help','env','install-hooks','clean','build','containerize','package','up','down','restart','rebuild','logs','ps','health')]
  [string]$Target = 'help'
)

$ErrorActionPreference = 'Stop'
$Compose    = 'docker compose'
$AgentImage = 'stockpredictor-agent:latest'
$UiImage    = 'stockpredictor-ui:latest'
$DistDir    = 'build'

function Invoke-Compose { param([string]$Args) Invoke-Expression "$Compose $Args" }

function Ensure-Env {
  if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
    Write-Host 'Created .env (edit it to add your API keys).' -ForegroundColor Yellow
  }
}

switch ($Target) {
  'help' {
    Write-Host 'Stock Predictor - available targets:' -ForegroundColor Cyan
    @(
      'env           Create .env from .env.example if missing',
      'install-hooks Install git hooks (keeps API keys out of commits)',
      'clean         Remove build artifacts, caches, and containers',
      'build         Build both service Docker images',
      'containerize  Alias for build',
      'package       Save built images as tarballs in ./build',
      'up            Build (if needed) and start both services',
      'down          Stop and remove services',
      'restart       Restart the stack',
      'rebuild       No-cache rebuild and restart',
      'logs          Follow logs',
      'ps            Show running services',
      'health        Curl the agent health endpoint'
    ) | ForEach-Object { Write-Host "  $_" }
  }
  'env' { Ensure-Env }
  'install-hooks' { & (Join-Path $PSScriptRoot 'scripts/install-hooks.ps1') }
  'clean' {
    try { Invoke-Compose 'down --remove-orphans' } catch { }
    foreach ($p in @($DistDir,'ui/dist','ui/node_modules','ui/.vite')) {
      if (Test-Path $p) { Remove-Item -Recurse -Force $p }
    }
    Get-ChildItem -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
      Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host 'Clean complete.' -ForegroundColor Green
  }
  { $_ -in 'build','containerize' } {
    Ensure-Env
    Invoke-Compose 'build agent'
    Invoke-Compose 'build ui'
    Write-Host 'Build complete.' -ForegroundColor Green
  }
  'package' {
    Ensure-Env
    Invoke-Compose 'build'
    if (-not (Test-Path $DistDir)) { New-Item -ItemType Directory -Path $DistDir | Out-Null }
    docker save $AgentImage -o "$DistDir/stockpredictor-agent.tar"
    docker save $UiImage    -o "$DistDir/stockpredictor-ui.tar"
    Write-Host "Packaged images into $DistDir/" -ForegroundColor Green
  }
  'up' {
    Ensure-Env
    Invoke-Compose 'up -d --build'
    $uiPort = $env:UI_PORT; if (-not $uiPort) { $uiPort = '3000' }
    $agPort = $env:AGENT_PORT; if (-not $agPort) { $agPort = '8000' }
    Write-Host "UI:    http://localhost:$uiPort" -ForegroundColor Cyan
    Write-Host "Agent: http://localhost:$agPort/health" -ForegroundColor Cyan
  }
  'down' { Invoke-Compose 'down' }
  'restart' { Invoke-Compose 'down'; Invoke-Compose 'up -d --build' }
  'rebuild' { Invoke-Compose 'build --no-cache'; Invoke-Compose 'up -d' }
  'logs' { Invoke-Compose 'logs -f' }
  'ps' { Invoke-Compose 'ps' }
  'health' {
    $agPort = $env:AGENT_PORT; if (-not $agPort) { $agPort = '8000' }
    Invoke-RestMethod "http://localhost:$agPort/health" | ConvertTo-Json
  }
}

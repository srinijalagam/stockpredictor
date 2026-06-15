# Install the project git hooks into .git/hooks (no git config changes).
$ErrorActionPreference = 'Stop'

$repoRoot = (git rev-parse --show-toplevel).Trim()
$src = Join-Path $repoRoot '.githooks'
$dst = Join-Path $repoRoot '.git/hooks'

New-Item -ItemType Directory -Force -Path $dst | Out-Null
Get-ChildItem -File $src | ForEach-Object {
  Copy-Item $_.FullName (Join-Path $dst $_.Name) -Force
  Write-Host "Installed $($_.Name) -> .git/hooks/$($_.Name)"
}
Write-Host 'Done. Git hooks are active.' -ForegroundColor Green

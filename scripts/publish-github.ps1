# Run in PowerShell from the extracted project directory, after reviewing the source.
# Requires Git + authenticated GitHub CLI: https://cli.github.com/
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Install Git for Windows first.' }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'Install GitHub CLI (gh) first.' }
gh auth status
if ($LASTEXITCODE -ne 0) { throw 'Run: gh auth login' }
if (-not (Test-Path '.git')) { git init -b main }
git add .
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m 'Initial VMESH-only MiniPool developer preview v0.1.0'
    if ($LASTEXITCODE -ne 0) { throw 'Git commit failed. Configure git user.name/user.email.' }
}
$repo='ati1993de/vargamesh-minipool'
gh repo view $repo *> $null
if ($LASTEXITCODE -ne 0) {
    gh repo create $repo --public --source . --remote origin --push --description 'Self-hosted VMESH SOLO pool for Bitaxe and SHA-256d ASICs. Windows GUI, local VargaMesh Core, Stratum V1, AuxPoW, fixed 1% fee; no Bitcoin node.'
    if ($LASTEXITCODE -ne 0) { throw 'GitHub repository creation failed.' }
} else {
    git remote get-url origin *> $null
    if ($LASTEXITCODE -ne 0) { git remote add origin "https://github.com/$repo.git" }
    git push -u origin main
    if ($LASTEXITCODE -ne 0) { throw 'Push failed.' }
}
gh repo edit $repo --homepage https://vargamesh.com/ --add-topic vargamesh,vmesh,bitaxe,solo-mining,sha256d,mining-pool,asic-mining,stratum,auxpow,windows-gui,cryptocurrency
Write-Host "Published: https://github.com/$repo"

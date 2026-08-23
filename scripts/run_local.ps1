param(
    [int]$Rows = 5000,
    [int]$Seed = 42
)

$ErrorActionPreference = "Stop"
$env:PYTHONPATH = Join-Path $PSScriptRoot "..\src"
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $projectRoot

python -m sentinelflow.cli generate --output data/raw/transactions.csv --rows $Rows --seed $Seed
python -m sentinelflow.cli train --data data/raw/transactions.csv --registry model-registry
python scripts/smoke_test.py
python scripts/api_smoke.py

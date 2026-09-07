[CmdletBinding()]
param(
    [int]$Port = 4180,
    [string]$CanaryHome = 'D:\FamilyStewardQmdCanary'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$env:FAMILY_STEWARD_QMD_BIN = Join-Path $CanaryHome 'runtime\node_modules\.bin\qmd.cmd'
$env:FAMILY_STEWARD_QMD_CONFIG_DIR = Join-Path $CanaryHome 'family-steward\config'
$env:FAMILY_STEWARD_QMD_CACHE_DIR = Join-Path $CanaryHome 'state\cache'

& (Join-Path $ProjectRoot '.venv\Scripts\python.exe') -m family_steward.web --port $Port

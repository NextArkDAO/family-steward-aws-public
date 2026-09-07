[CmdletBinding()]
param(
    [string]$CanaryHome = 'D:\FamilyStewardQmdCanary'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$Corpus = Join-Path $ProjectRoot 'fixtures\qmd-corpus'
$Qmd = Join-Path $CanaryHome 'runtime\node_modules\.bin\qmd.cmd'
$Config = Join-Path $CanaryHome 'family-steward\config'
$Cache = Join-Path $CanaryHome 'state\cache'

foreach ($required in @($Corpus, $Qmd, $Cache)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Family Steward QMD requirement is unavailable: $required"
    }
}

New-Item -ItemType Directory -Force -Path $Config | Out-Null
$normalizedCorpus = $Corpus.Replace('\', '/')
$configuration = @"
collections:
  family-steward-v0:
    path: $normalizedCorpus
    pattern: "**/*.md"
models:
  embed: hf:ggml-org/embeddinggemma-300M-GGUF/embeddinggemma-300M-Q8_0.gguf
  generate: hf:tobil/qmd-query-expansion-1.7B-gguf/qmd-query-expansion-1.7B-q4_k_m.gguf
  rerank: hf:ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF/qwen3-reranker-0.6b-q8_0.gguf
"@
Set-Content -LiteralPath (Join-Path $Config 'family-steward.yml') -Value $configuration -Encoding utf8NoBOM

$env:QMD_CONFIG_DIR = $Config
$env:XDG_CACHE_HOME = $Cache
$env:QMD_EMBED_PARALLELISM = '1'

$version = (& $Qmd --version | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $version -ne 'qmd 2.8.3 (facd35e)') {
    throw "Unexpected QMD build: $version"
}

& $Qmd --index family-steward update
if ($LASTEXITCODE -ne 0) { throw 'Family Steward QMD update failed.' }
& $Qmd --index family-steward embed -c family-steward-v0 --timeout 10
if ($LASTEXITCODE -ne 0) { throw 'Family Steward QMD embedding failed.' }

[pscustomobject]@{
    qmd_binary = $Qmd
    qmd_config_dir = $Config
    qmd_cache_dir = $Cache
    collection = 'family-steward-v0'
    index = 'family-steward'
    mode = 'on-demand-cli'
} | ConvertTo-Json

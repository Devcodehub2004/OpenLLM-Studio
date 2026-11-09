# OpenLLM Studio: read-only local demo readiness check (Windows PowerShell 5.1+)
# Run from the repository root after starting Ollama, FastAPI and Streamlit.
# This script never sends model prompts, reads chat data, changes settings or downloads models.
[CmdletBinding()]
param(
    [ValidateRange(1,65535)][int]$ApiPort = 8000,
    [ValidateRange(1,65535)][int]$UiPort = 8501,
    [ValidateRange(1,65535)][int]$OllamaPort = 11434
)
$ErrorActionPreference = 'Stop'
$failed = $false

function Get-LocalJson {
    param([string]$Url, [string]$Label)
    try {
        $data = Invoke-RestMethod -Method Get -Uri $Url -TimeoutSec 6
        Write-Host "[OK] $Label" -ForegroundColor Green
        return $data
    } catch {
        Write-Host "[FAIL] $Label at $Url" -ForegroundColor Red
        Write-Host ("       " + $_.Exception.Message)
        $script:failed = $true
        return $null
    }
}

# 1. Ollama is serving, and at least one model is installed.
$ollama = Get-LocalJson -Url "http://127.0.0.1:${OllamaPort}/api/tags" -Label "Ollama model service"
if ($null -ne $ollama) {
    $names = @($ollama.models | ForEach-Object { $_.name } | Where-Object { $_ })
    if ($names.Count -eq 0) {
        Write-Host "[WARN] No Ollama models installed. Install one before an inference demo." -ForegroundColor Yellow
    } else {
        Write-Host ("       Installed models: " + ($names -join ', '))
    }
}

# 2. FastAPI root health and available-model endpoint.
$health = Get-LocalJson -Url "http://127.0.0.1:${ApiPort}/" -Label "FastAPI root endpoint"
if ($null -ne $health -and $health.status -ne "OpenLLM Studio is running") {
    Write-Host "[WARN] FastAPI response did not match expected OpenLLM Studio status." -ForegroundColor Yellow
}
$apiModels = Get-LocalJson -Url "http://127.0.0.1:${ApiPort}/models" -Label "FastAPI to Ollama model lookup"
if ($null -ne $apiModels -and @($apiModels.models).Count -eq 0) {
    Write-Host "[WARN] FastAPI reports no available models." -ForegroundColor Yellow
}

# 3. Streamlit's built-in readiness endpoint (not a screenshot or full UI test).
try {
    $ui = Invoke-WebRequest -Method Get -Uri "http://127.0.0.1:${UiPort}/_stcore/health" -TimeoutSec 6 -UseBasicParsing
    if ($ui.StatusCode -ne 200) { throw "Unexpected status code $($ui.StatusCode)" }
    Write-Host "[OK] Streamlit server health" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Streamlit health at http://127.0.0.1:${UiPort}/_stcore/health" -ForegroundColor Red
    Write-Host ("       " + $_.Exception.Message)
    $failed = $true
}

if ($failed) {
    Write-Host "Some local services are unavailable. Follow README setup steps before recording." -ForegroundColor Red
    exit 1
}
Write-Host "Services respond locally. Next: manually test chat streaming, history and export in the browser." -ForegroundColor Green
exit 0

<#
Run from an isolated checkout of the exact frozen GA validation branch.
Usage:
 .\RUN_FIXED_2000_VALIDATION.ps1 -RepoPath 'C:\path\to\isolated\_val4' -ArchivePath 'D:\research\independent_validation_fixed_2000' -AuthorizationPath 'C:\path\to\AUTHORIZATION_FIXED_2000_20261010.json'
The initial archive must be new/empty, or a legitimately existing archive
from the SAME run with RUN_IDENTITY.json for resume. Never delete latches.
#>
param(
    [Parameter(Mandatory=$true)][string]$RepoPath,
    [Parameter(Mandatory=$true)][string]$ArchivePath,
    [Parameter(Mandatory=$true)][string]$AuthorizationPath,
    [string]$PythonExe = (Join-Path $env:USERPROFILE 'anaconda3\python.exe')
)
$ErrorActionPreference = 'Stop'
$ExpectedCommit = 'c178bff7f924257b33f1e8c17e0d5e59a1fe68e9'
$ExpectedFreezeHash = '45d157c0a3b9460d7c29e389b649afef0f0e6bc568bfba8eb773f9b5b974ae15'
$FreezeRelativePath = 'results/diagnostics/independent_validation_ready_20261010/FINAL_VALIDATION_FREEZE_RECEIPT.json'

if (-not (Test-Path -LiteralPath $RepoPath -PathType Container)) { throw "Repository does not exist: $RepoPath" }
if (-not (Test-Path -LiteralPath $AuthorizationPath -PathType Leaf)) { throw "Authorization file does not exist: $AuthorizationPath" }
if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) { throw "Python executable does not exist: $PythonExe" }
$ObservedCommit = (& git -C $RepoPath rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $ObservedCommit -ne $ExpectedCommit) {
    throw "Checkout HEAD must be exactly frozen commit $ExpectedCommit; got $ObservedCommit. Do not silently re-freeze."
}
$FreezeFile = Join-Path $RepoPath $FreezeRelativePath
$ActualFreezeHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $FreezeFile).Hash.ToLower()
if ($ActualFreezeHash -ne $ExpectedFreezeHash) { throw "Freeze receipt mismatch; refusing to proceed." }
$Approval = Get-Content -LiteralPath $AuthorizationPath -Raw | ConvertFrom-Json
if ($Approval.authorization_type -ne 'EXPLICIT_AUTHOR_APPROVAL_FOR_FIXED_2000_VALIDATION' -or
    $Approval.verbatim_author_request -ne 'yes' -or
    $Approval.freeze_sha256 -ne $ExpectedFreezeHash -or
    $Approval.sample_size -ne 2000 -or
    $Approval.allow_policy_reselection -ne $false) { throw "Authorization field mismatch." }

$env:PYTHONPATH='src'
$env:NUMBA_CACHE_DIR=Join-Path $env:TEMP 'val4-20261010-numba'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:NUMBA_NUM_THREADS='1'
Push-Location $RepoPath
try {
    & $PythonExe -m la_grid.diagnostics.independent_validation_20261010 verify
    if ($LASTEXITCODE -ne 0) { throw 'Frozen receipt / protected checkout preflight failed.' }
    $ArchiveParent = Split-Path -Parent $ArchivePath
    if (-not (Test-Path -LiteralPath $ArchiveParent -PathType Container)) { throw "Create a dedicated external archive parent directory first: $ArchiveParent" }
    & $PythonExe -m la_grid.diagnostics.independent_validation_20261010 execute --authorization $AuthorizationPath --archive $ArchivePath
    if ($LASTEXITCODE -ne 0) { throw 'Independent validation failed or stopped for manual review. Do not redraw or change the frozen settings.' }
    $ReceiptFile = Join-Path $ArchivePath 'REPRODUCIBILITY_RECEIPT.json'
    if (-not (Test-Path -LiteralPath $ReceiptFile)) { throw 'Missing completion receipt. Do not report results as complete.' }
    $Receipt = Get-Content -LiteralPath $ReceiptFile -Raw | ConvertFrom-Json
    if ($Receipt.status -ne 'INDEPENDENT_VALIDATION_COMPLETED' -or $Receipt.sample_count -ne 2000 -or $Receipt.unique_physical_hashes -ne 2000 -or $Receipt.policy_count -ne 13) {
        throw 'Completion receipt did not certify 2000 unique samples x 13 policies.'
    }
    Write-Output "VALIDATION COMPLETED. Receipt: $ReceiptFile"
    Write-Output "Primary paired effect: $(Join-Path $ArchivePath 'PRIMARY_PAIRED_EFFECT.csv')"
}
finally {
    Pop-Location
}

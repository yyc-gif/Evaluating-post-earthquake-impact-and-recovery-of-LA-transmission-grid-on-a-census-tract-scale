param([string]$Python = "$env:USERPROFILE\anaconda3\python.exe")
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
$Package = 'docs/data_research/stage7_path_b_p2_integration_review_20261014'
Push-Location -LiteralPath $Root
try {
    foreach ($Script in @('analyze_path_b.py','make_review_figures.py','independent_qa.py')) {
        $Relative = "$Package/$Script"
        $Flags = if ($Script -eq 'make_review_figures.py') { '' } else { '--archived-inputs' }
        & $Python -c "import os,sys,runpy;sys.argv=['$Script','$Flags'];runpy.run_path('\\\\?\\'+os.path.abspath('$Relative'),run_name='__main__')"
        if ($LASTEXITCODE -ne 0) { throw "Review reproduction failed: $Script" }
    }
} finally {
    Pop-Location
}

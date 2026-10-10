param([Parameter(Mandatory=$true)][string]$Package, [Parameter(Mandatory=$true)][string]$Scratch)
$ErrorActionPreference = 'Stop'
$packageRoot = (Resolve-Path -LiteralPath $Package).Path
$workspaceRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..')).Path
$scratchRoot = [IO.Path]::GetFullPath($Scratch)
if (-not $scratchRoot.StartsWith($workspaceRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Scratch must stay within isolated worktree' }
New-Item -ItemType Directory -Path $scratchRoot -Force | Out-Null
$inventory = Get-Content -LiteralPath (Join-Path $packageRoot 'MANUSCRIPT_SOURCE_INVENTORY.json') -Raw | ConvertFrom-Json
$source = ($inventory | Where-Object source_id -eq 'S19').path
$review = Join-Path $packageRoot 'Manuscript_Stage7_Integration_REVIEW.docx'
Copy-Item -LiteralPath $source -Destination (Join-Path $scratchRoot 'source.docx')
Copy-Item -LiteralPath $review -Destination (Join-Path $scratchRoot 'review.docx')
$word = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $version = $word.Version
    foreach ($stem in @('source','review')) {
        $document = $null
        try {
            $inputFile = Join-Path $scratchRoot ($stem + '.docx')
            $outputFile = Join-Path $scratchRoot ($stem + '.pdf')
            $document = $word.Documents.Open($inputFile, $false, $true, $false)
            $document.Repaginate()
            $document.ExportAsFixedFormat($outputFile, 17)
            Write-Output "$stem exported with Microsoft Word $version"
        } finally {
            if ($null -ne $document) { $document.Close(0); [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($document) }
        }
    }
} finally {
    if ($null -ne $word) { $word.Quit(); [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) }
}
Copy-Item -LiteralPath (Join-Path $scratchRoot 'review.pdf') -Destination (Join-Path $packageRoot 'Manuscript_Stage7_Integration_REVIEW.pdf')
@{ renderer = 'Microsoft Word COM ExportAsFixedFormat'; version = $version; read_only = $true; original_source_overwritten = $false; canonical_renderer_limitation = 'render_docx.py failed: soffice.exe absent and long Windows paths; Word native export used instead'; date = '2026-10-10' } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $packageRoot 'NATIVE_RENDERER_RECORD.json') -Encoding utf8

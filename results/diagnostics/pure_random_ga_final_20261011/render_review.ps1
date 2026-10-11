$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path (Split-Path $PSScriptRoot))
$review = Join-Path $root 'Review_and_Revision\Pure_Random_GA_20261011'
$python = 'C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$poppler = 'C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe'
$renderer = 'C:\Users\yinch\.codex\plugins\cache\openai-primary-runtime\documents\26.1009.11318\skills\documents\render_docx.py'
$qa = Join-Path $env:TEMP 'gaf12_render_20261011'
[void][System.IO.Directory]::CreateDirectory($qa)
$docx = Join-Path $qa 'review.docx'
[System.IO.File]::Copy((Join-Path $review 'Manuscript_Random_GA_Validation_REVIEW.docx'), $docx, $true)
$attempt = Join-Path $qa 'packaged_renderer'
$oldPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$log = & $python -B $renderer $docx --output_dir $attempt --emit_pdf 2>&1
$rendererExit = $LASTEXITCODE
$ErrorActionPreference = $oldPreference
[System.IO.File]::WriteAllLines((Join-Path $qa 'packaged_renderer.log'), [string[]]$log)
Write-Output "PACKAGED_RENDERER_EXIT $rendererExit"
if ($rendererExit -ne 0) {
    Write-Output ($log | Select-Object -Last 12)
    # Read-only native Word export; never save either manuscript or terminate existing Word.
    $word = $null
    $document = $null
    try {
        $word = New-Object -ComObject Word.Application
        $word.Visible = $false
        $word.DisplayAlerts = 0
        $word.AutomationSecurity = 3
        $document = $word.Documents.Open($docx, $false, $true)
        $document.Repaginate()
        $pdf = Join-Path $qa 'review.pdf'
        $document.ExportAsFixedFormat($pdf, 17)
        $pages = $document.ComputeStatistics(2)
        Write-Output "NATIVE_WORD_PAGES $pages"
    } finally {
        if ($null -ne $document) { $document.Close(0) }
        if ($null -ne $word) { $word.Quit() }
    }
    & $poppler -png -r 120 $pdf (Join-Path $qa 'page')
    if ($LASTEXITCODE -ne 0) { throw 'Poppler document rendering failed' }
} else {
    Write-Output 'PACKAGED_RENDERER_PASSED'
}
foreach ($name in @('FIG_GA_RECOVERY', 'FIG_GA_POPULATION_LOSS', 'FIG_GA_HOSPITAL_LOSS', 'FIG_GA_EQUITY')) {
    $shortPdf = Join-Path $qa ($name + '.pdf')
    [System.IO.File]::Copy((Join-Path $PSScriptRoot ('artwork\' + $name + '.pdf')), $shortPdf, $true)
    & $poppler -png -r 150 -singlefile $shortPdf (Join-Path $qa $name)
    if ($LASTEXITCODE -ne 0) { throw "Figure rendering failed: $name" }
}
Write-Output "QA_RENDER_DIRECTORY $qa"

param([ValidateSet('Word','WPS')][string]$Engine='Word', [string]$RenderDirectory='qa')
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$word = $null
try {
    Write-Output ('Starting isolated read-only renderer: ' + $Engine)
    $class = if ($Engine -eq 'WPS') { 'kwps.Application' } else { 'Word.Application' }
    $word = New-Object -ComObject $class
    Write-Output 'Automation instance created'
    if ($word.Documents.Count -ne 0) {
        $word = $null
        throw 'Refusing to use a Word instance with existing user documents.'
    }
    $word.Visible = $false
    $word.DisplayAlerts = 0
    if ($Engine -eq 'Word') { $word.AutomationSecurity = 3 }
    foreach ($item in @(
        @{Source='PART_V_Figure_Structure_Checked.docx'; Output='structure'},
        @{Source='Path_B_Figure_Captions_Checked.docx'; Output='captions'}
    )) {
        $path = Join-Path $root $item.Source
        $dir = Join-Path $root $RenderDirectory
        if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
        $pdf = Join-Path $dir ($item.Output + '.pdf')
        if (Test-Path -LiteralPath $pdf) { throw "Refusing to replace prior render: $pdf" }
        $document = $null
        try {
            Write-Output ('Opening read-only copy: ' + $item.Source)
            $document = $word.Documents.Open($path, $false, $true, $false)
            Write-Output 'Opened; paginating'
            $document.Repaginate()
            $pages = $document.ComputeStatistics(2)
            $document.ExportAsFixedFormat($pdf, 17)
            Write-Output ($item.Output + ': ' + $pages + ' pages; read-only ' + $Engine + ' PDF render')
        } finally {
            if ($null -ne $document) { $document.Close(0) }
        }
    }
} finally {
    if ($null -ne $word) {
        if ($Engine -eq 'WPS') {
            $discard = 0
            $word.Quit([ref]$discard)
        } else { $word.Quit(0) }
    }
}

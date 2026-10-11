param([Parameter(Mandatory=$true)][string]$RenderDirectory,[switch]$ReviewOnly)
$ErrorActionPreference='Stop'
$taskRender=(Resolve-Path -LiteralPath $RenderDirectory).Path
$word=$null
try {
    $word=New-Object -ComObject Word.Application
    $word.Visible=$false
    $word.DisplayAlerts=0
    $taskNames=if($ReviewOnly){@('review')}else{@('source','review')}
    foreach($name in $taskNames) {
        $taskDocPath=Join-Path $taskRender ($name+'.docx')
        $taskPdfPath=Join-Path $taskRender ($name+'.pdf')
        $document=$word.Documents.Open($taskDocPath,$false,$true)
        try {
            $document.ExportAsFixedFormat($taskPdfPath,17)
            Write-Output ($name+': '+$document.ComputeStatistics(2)+' pages')
        } finally {
            $document.Close(0)
            [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($document)
        }
    }
} finally {
    if($null -ne $word) {
        $word.Quit()
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($word)
    }
}

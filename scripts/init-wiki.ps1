param([Parameter(Mandatory=$true)][string]$WikiPath)
$ErrorActionPreference = 'Stop'
$seedRoot = Join-Path $PSScriptRoot '../wiki-seed'
$wikiRoot = [System.IO.Path]::GetFullPath($WikiPath)
New-Item -ItemType Directory -Force -Path $wikiRoot | Out-Null
foreach ($folder in @('00_Home','10_Research','20_Strategies','30_Decisions','40_Daily/Generated','50_Reviews','90_Templates')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $wikiRoot $folder) | Out-Null
}
foreach ($source in Get-ChildItem -LiteralPath $seedRoot -File -Recurse) {
    $relative = $source.FullName.Substring((Get-Item $seedRoot).FullName.Length + 1)
    $destination = Join-Path $wikiRoot $relative
    if (-not (Test-Path -LiteralPath $destination)) {
        Copy-Item -LiteralPath $source.FullName -Destination $destination
    }
}
Write-Output 'Wiki scaffold installed; existing notes preserved.'

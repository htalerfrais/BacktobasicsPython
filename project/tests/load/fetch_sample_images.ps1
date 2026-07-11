# Downloads sample JPEGs for Locust load tests into assets/coco_samples/ (gitignored).
$ErrorActionPreference = "Stop"

$dest = Join-Path $PSScriptRoot "assets\coco_samples"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$seeds = 1..10
foreach ($seed in $seeds) {
    $out = Join-Path $dest "sample_$seed.jpg"
    if (Test-Path $out) {
        Write-Host "Skip existing $out"
        continue
    }
    $url = "https://picsum.photos/seed/backtobasics$seed/640/480.jpg"
    Write-Host "Downloading $url -> $out"
    Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing
}

Write-Host "Done. $($seeds.Count) images in $dest"

param(
    [string]$Python = "$PSScriptRoot\..\.venv\Scripts\python.exe"
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path -LiteralPath "$PSScriptRoot\..").Path
Push-Location $repo
try {
    & $Python -m PyInstaller --noconfirm --onefile --windowed --noupx `
        --name Boxhead --paths "$repo\src" --add-data "${repo}/assets:boxhead/data" `
        --specpath build --workpath build/pyinstaller --distpath dist `
        src/boxhead/__main__.py
    if ($LASTEXITCODE -ne 0) { throw 'Windows build failed.' }
    Compress-Archive -LiteralPath @("$repo\dist\Boxhead.exe", "$repo\docs\PLAY-WINDOWS.txt") `
        -DestinationPath "$repo\dist\Boxhead-Windows.zip" -Force
    Write-Output "Ready to share: $repo\dist\Boxhead-Windows.zip"
} finally {
    Pop-Location
}

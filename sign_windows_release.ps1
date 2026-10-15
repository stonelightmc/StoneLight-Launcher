param(
    [string]$Thumbprint = ""
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$config = Get-Content -Raw "config.json" | ConvertFrom-Json
$version = [string]$config.launcher_version
if ([string]::IsNullOrWhiteSpace($version)) {
    throw "launcher_version is missing in config.json."
}

$exePath = Join-Path $PSScriptRoot "dist\StoneLight Launcher\StoneLight Launcher.exe"
if (-not (Test-Path $exePath)) {
    throw "Executable not found. Run build_windows_exe.cmd first: $exePath"
}

$windowsKitsRoots = @(
    "${env:ProgramFiles(x86)}\Windows Kits\10\bin",
    "$env:ProgramFiles\Windows Kits\10\bin"
) | Where-Object { $_ -and (Test-Path $_) }

$signTool = $windowsKitsRoots |
    ForEach-Object { Get-ChildItem -Path $_ -Filter "signtool.exe" -File -Recurse -ErrorAction SilentlyContinue } |
    Where-Object { $_.FullName -match "\\x64\\signtool\.exe$" } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $signTool) {
    throw "SignTool.exe (x64) was not found. Install Windows SDK Signing Tools for Desktop Apps."
}

$signArguments = @(
    "sign",
    "/fd", "SHA256",
    "/tr", "http://time.certum.pl",
    "/td", "SHA256",
    "/d", "StoneLight Launcher",
    "/du", "https://github.com/stonelightmc/StoneLight-Launcher"
)

if ([string]::IsNullOrWhiteSpace($Thumbprint)) {
    $signArguments += "/a"
} else {
    $normalizedThumbprint = $Thumbprint.Replace(" ", "")
    $signArguments += @("/sha1", $normalizedThumbprint)
}

$signArguments += $exePath

Write-Host "Signing StoneLight Launcher $version..."
& $signTool.FullName @signArguments
if ($LASTEXITCODE -ne 0) {
    throw "SignTool failed with exit code $LASTEXITCODE."
}

Write-Host "Verifying Authenticode signature..."
& $signTool.FullName "verify" "/pa" "/all" "/v" $exePath
if ($LASTEXITCODE -ne 0) {
    throw "Signature verification failed with exit code $LASTEXITCODE."
}

$versionInfo = (Get-Item $exePath).VersionInfo
Write-Host "File version: $($versionInfo.FileVersion)"
Write-Host "Product version: $($versionInfo.ProductVersion)"

$archiveVersion = $version.Replace(".", "_")
$archivePath = Join-Path $PSScriptRoot "StoneLightLauncher_v${archiveVersion}_Windows.zip"
if (Test-Path $archivePath) {
    Remove-Item $archivePath -Force
}

Write-Host "Creating signed release archive..."
Compress-Archive -Path (Join-Path $PSScriptRoot "dist\StoneLight Launcher\*") -DestinationPath $archivePath

Write-Host "Signed release is ready:"
Write-Host "  $archivePath"

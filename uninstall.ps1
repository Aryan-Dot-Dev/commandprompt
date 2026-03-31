# Windows uninstaller for nlsh
# Run this script in PowerShell to uninstall nlsh

$ErrorActionPreference = "Stop"

Write-Host "Uninstalling nlsh..."

$INSTALL_DIR = "$env:USERPROFILE\.nlsh"
$LOCAL_BIN = "$env:USERPROFILE\.local\bin"

# Remove install directory
if (Test-Path $INSTALL_DIR) {
    Remove-Item -Recurse -Force $INSTALL_DIR
    Write-Host "Removed installation directory"
}

# Remove bin files
if (Test-Path "$LOCAL_BIN\nlsh.bat") {
    Remove-Item -Force "$LOCAL_BIN\nlsh.bat"
}
if (Test-Path "$LOCAL_BIN\nlsh.ps1") {
    Remove-Item -Force "$LOCAL_BIN\nlsh.ps1"
}

# Remove from PowerShell profile
$profilePath = $PROFILE.CurrentUserAllHosts
if (Test-Path $profilePath) {
    $profileContent = Get-Content $profilePath -Raw
    
    # Remove nlsh configuration lines
    $profileContent = $profileContent -replace "(\r?\n)?# nlsh - PATH(\r?\n)?", "`n"
    $profileContent = $profileContent -replace '(\r?\n)?[^\n]*\.local\\bin[^\n]*(\r?\n)?', "`n"
    $profileContent = $profileContent -replace "(\r?\n)?# nlsh - auto-start.*?# nlsh(\r?\n)?", "`n"
    $profileContent = $profileContent -replace "(\r?\n)?# Uncomment below to auto-launch.*?(\r?\n)?", "`n"
    $profileContent = $profileContent -replace "(\r?\n)?# nlsh(\r?\n)?", "`n"
    
    # Clean up extra blank lines
    $profileContent = $profileContent -replace "(\r?\n){3,}", "`n`n"
    
    $profileContent | Set-Content $profilePath -Encoding UTF8
    Write-Host "Removed from PowerShell profile"
}

# Remove from PATH environment variable
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($currentPath -like "*$LOCAL_BIN*") {
    $newPath = $currentPath -replace [regex]::Escape($LOCAL_BIN) + ";?", ""
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    Write-Host "Removed from PATH"
}

Write-Host ""
Write-Host "nlsh has been uninstalled"
Write-Host ""

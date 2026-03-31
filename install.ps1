# Windows installer for nlsh
# Run this script in PowerShell to install nlsh on Windows

$ErrorActionPreference = "Stop"

$INSTALL_DIR = "$env:USERPROFILE\.nlsh"
$REPO_URL = "https://github.com/Aryan-Dot-Dev/commandprompt.git"
$LOCAL_BIN = "$env:USERPROFILE\.local\bin"

Write-Host "Installing nlsh..."

# Check if Python 3 is installed
if (-not (Get-Command python3 -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Host "Python 3 is required. Please install it first."
        Write-Host "Download from: https://www.python.org/downloads/"
        exit 1
    }
}

# Clone or update repository
if (Test-Path $INSTALL_DIR) {
    Write-Host "Updating existing installation..."
    Push-Location $INSTALL_DIR
    git pull --quiet
    Pop-Location
} else {
    Write-Host "Downloading nlsh..."
    git clone --quiet $REPO_URL $INSTALL_DIR
}

Push-Location $INSTALL_DIR

# Setup Python environment
Write-Host "Setting up Python environment..."
python -m venv venv
& ".\venv\Scripts\Activate.ps1"
python -m pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
Deactivate

# Create nlsh command
Write-Host "Creating nlsh command..."
$null = New-Item -ItemType Directory -Path $LOCAL_BIN -Force

# Create empty .env file for configuration
$env_file = Join-Path $INSTALL_DIR ".env"
if (-not (Test-Path $env_file)) {
    @"
# nlsh environment configuration
# Add your API keys here
"@ | Set-Content $env_file -Encoding UTF8
}

# Create Windows batch wrapper
$nlsh_bat_content = @"
@echo off
cd /d "%USERPROFILE%\.nlsh"
call venv\Scripts\activate.bat
python nlsh.py %*
"@

$nlsh_bat_content | Set-Content "$LOCAL_BIN\nlsh.bat" -Encoding ASCII

# Create PowerShell wrapper
$nlsh_ps1_content = @"
# nlsh launcher for PowerShell
& "$env:USERPROFILE\.nlsh\venv\Scripts\Activate.ps1"
python "$env:USERPROFILE\.nlsh\nlsh.py" @args
"@

$nlsh_ps1_content | Set-Content "$LOCAL_BIN\nlsh.ps1" -Encoding UTF8

# Setup PATH environment variable
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($currentPath -notlike "*$LOCAL_BIN*") {
    Write-Host "Adding $LOCAL_BIN to PATH..."
    $newPath = "$LOCAL_BIN;$currentPath"
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
}

# Setup PowerShell profile
function Setup-PowerShellProfile {
    $profilePath = $PROFILE.CurrentUserAllHosts
    $profileDir = Split-Path -Parent $profilePath
    
    if (-not (Test-Path $profileDir)) {
        New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    }
    
    if (-not (Test-Path $profilePath)) {
        New-Item -ItemType File -Path $profilePath -Force | Out-Null
    }
    
    $profileContent = @()
    
    if (Test-Path $profilePath) {
        $profileContent = @(Get-Content $profilePath -ErrorAction SilentlyContinue | Where-Object { $_ })
    }
    
    # Check if nlsh config already exists
    $hasNlshConfig = $profileContent -match "nlsh"
    
    if (-not $hasNlshConfig) {
    $profileContent += "`n"
    $profileContent += "# nlsh - PATH`n"
    $profileContent += "`$env:PATH = `"$LOCAL_BIN;`$env:PATH`"`n"
    $profileContent += "`n"
    $profileContent += "# nlsh - auto-start (remove this section to disable)`n"
    $profileContent += "# Uncomment below to auto-launch nlsh on PowerShell startup`n"
    $profileContent += "# nlsh`n"
    Write-Host "Added nlsh configuration to PowerShell profile"
}
    
    $profileContent -join "`n" | Set-Content $profilePath -Encoding UTF8 -NoNewline
}

Setup-PowerShellProfile

Pop-Location

Write-Host ""
Write-Host "nlsh installed successfully!"
Write-Host ""
Write-Host "To start using nlsh:"
Write-Host "1. Command Prompt: nlsh"
Write-Host "2. PowerShell: nlsh.ps1"
Write-Host ""
Write-Host "You may need to close and reopen your terminal for PATH changes to take effect."
Write-Host ""

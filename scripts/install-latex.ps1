# ──────────────────────────────────────────────────────────
#  LaTeX Installation Script for ResumeGen (Windows)
#  Installs MiKTeX — lightweight LaTeX distribution
# ──────────────────────────────────────────────────────────
#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

function Write-Info  ($msg) { Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function Write-Ok    ($msg) { Write-Host "[OK]    $msg" -ForegroundColor Green }
function Write-Warn  ($msg) { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Write-Err   ($msg) { Write-Host "[ERR]   $msg" -ForegroundColor Red }

# ── Pre-flight check ──────────────────────────────────────
$pdflatex = Get-Command pdflatex -ErrorAction SilentlyContinue
if ($pdflatex) {
    Write-Ok "pdflatex is already installed: $($pdflatex.Source)"
    exit 0
}

Write-Info "pdflatex not found — installing MiKTeX..."

# ── Check for package managers ────────────────────────────
$installer = $null

if (Get-Command winget -ErrorAction SilentlyContinue) {
    $installer = "winget"
} elseif (Get-Command choco -ErrorAction SilentlyContinue) {
    $installer = "choco"
} elseif (Get-Command scoop -ErrorAction SilentlyContinue) {
    $installer = "scoop"
}

switch ($installer) {
    "winget" {
        Write-Info "Installing MiKTeX via winget..."
        winget install --id MiKTeX.MiKTeX --accept-package-agreements --accept-source-agreements
    }
    "choco" {
        Write-Info "Installing MiKTeX via Chocolatey..."
        choco install miktex -y
    }
    "scoop" {
        Write-Info "Installing MiKTeX via Scoop..."
        scoop bucket add extras
        scoop install miktex
    }
    default {
        Write-Info "No package manager found. Downloading MiKTeX installer..."

        $miktexUrl = "https://miktex.org/download/ctan/systems/win32/miktex/setup/windows-x64/basic-miktex-24.1-x64.exe"
        $tempInstaller = Join-Path $env:TEMP "miktex-setup.exe"

        Write-Info "Downloading from $miktexUrl ..."
        Invoke-WebRequest -Uri $miktexUrl -OutFile $tempInstaller -UseBasicParsing

        Write-Info "Running MiKTeX installer (unattended)..."
        Start-Process -FilePath $tempInstaller `
            -ArgumentList "--unattended", "--auto-install=yes" `
            -Wait -NoNewWindow

        Remove-Item $tempInstaller -Force -ErrorAction SilentlyContinue
    }
}

# ── Refresh PATH ──────────────────────────────────────────
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" `
          + [System.Environment]::GetEnvironmentVariable("Path", "User")

# ── Verify ────────────────────────────────────────────────
$pdflatex = Get-Command pdflatex -ErrorAction SilentlyContinue
if ($pdflatex) {
    Write-Ok "LaTeX installed successfully!"
    Write-Info "Location: $($pdflatex.Source)"

    # Enable auto-install of missing packages
    Write-Info "Configuring MiKTeX to auto-install missing packages..."
    try {
        initexmf --set-config-value "[MPM]AutoInstall=1" 2>$null
        Write-Ok "Auto-install enabled — missing LaTeX packages will be downloaded on demand."
    } catch {
        Write-Warn "Could not enable auto-install. You may need to install packages manually via MiKTeX Console."
    }
} else {
    Write-Warn "pdflatex not found in PATH after installation."
    Write-Warn "Please restart your terminal or add MiKTeX to your PATH manually."
    Write-Warn "Default location: C:\Program Files\MiKTeX\miktex\bin\x64\"
}

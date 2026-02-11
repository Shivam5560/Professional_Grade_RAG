#!/bin/bash
# ──────────────────────────────────────────────────────────
#  LaTeX Installation Script for ResumeGen
#  Supports: macOS (Homebrew) · Ubuntu/Debian · Fedora/RHEL
# ──────────────────────────────────────────────────────────
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $1"; }
success() { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error()   { echo -e "${RED}[ERR]${NC}   $1"; }

# ── Pre-flight check ──────────────────────────────────────
if command -v pdflatex &>/dev/null; then
    success "pdflatex is already installed: $(pdflatex --version | head -1)"
    exit 0
fi

info "pdflatex not found — installing LaTeX distribution..."

# ── Detect OS ─────────────────────────────────────────────
OS="$(uname -s)"

case "$OS" in
    Darwin)
        info "Detected macOS"

        if ! command -v brew &>/dev/null; then
            error "Homebrew is required. Install it first:"
            echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi

        info "Installing BasicTeX via Homebrew (compact ~100 MB)..."
        brew install --cask basictex

        # Add TeX Live to PATH for the current session
        eval "$(/usr/libexec/path_helper)"
        export PATH="/Library/TeX/texbin:$PATH"

        # Install packages needed by ResumeGen templates
        info "Installing required LaTeX packages..."
        sudo tlmgr update --self
        sudo tlmgr install \
            enumitem \
            titlesec \
            geometry \
            hyperref \
            fontenc \
            inputenc \
            xcolor \
            parskip \
            fancyhdr \
            lastpage \
            multicol \
            tabularx \
            latexmk
        ;;

    Linux)
        info "Detected Linux"

        if command -v apt-get &>/dev/null; then
            info "Using apt (Debian/Ubuntu)..."
            sudo apt-get update -qq
            sudo apt-get install -y -qq \
                texlive-latex-base \
                texlive-latex-extra \
                texlive-fonts-recommended \
                texlive-latex-recommended \
                latexmk

        elif command -v dnf &>/dev/null; then
            info "Using dnf (Fedora/RHEL)..."
            sudo dnf install -y \
                texlive-scheme-basic \
                texlive-latex \
                texlive-collection-latexextra \
                texlive-collection-fontsrecommended \
                latexmk

        elif command -v yum &>/dev/null; then
            info "Using yum (CentOS/older RHEL)..."
            sudo yum install -y \
                texlive-latex \
                texlive-collection-latexextra \
                texlive-collection-fontsrecommended \
                latexmk

        elif command -v pacman &>/dev/null; then
            info "Using pacman (Arch Linux)..."
            sudo pacman -S --noconfirm \
                texlive-core \
                texlive-latexextra \
                texlive-fontsrecommended \
                latexmk

        else
            error "Unsupported package manager. Please install TeX Live manually:"
            echo "  https://tug.org/texlive/"
            exit 1
        fi
        ;;

    *)
        error "Unsupported OS: $OS"
        echo "Use the PowerShell script for Windows: scripts/install-latex.ps1"
        exit 1
        ;;
esac

# ── Verify ────────────────────────────────────────────────
if command -v pdflatex &>/dev/null; then
    success "LaTeX installed successfully!"
    info "$(pdflatex --version | head -1)"
else
    warn "pdflatex not found in PATH. You may need to restart your terminal."
    warn "On macOS, try: export PATH=\"/Library/TeX/texbin:\$PATH\""
fi

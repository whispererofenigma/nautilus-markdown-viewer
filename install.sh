#!/usr/bin/env bash
# ==============================================================================
# Nautilus Markdown Viewer & Side Panel - Installation Script
# https://github.com/whispererofenigma/nautilus-markdown-viewer
# ==============================================================================

set -e

# Terminal colors
BOLD="\033[1m"
GREEN="\033[1;32m"
BLUE="\033[1;34m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}====================================================${RESET}"
echo -e "${BOLD}${BLUE}  Installing Nautilus Markdown Viewer & Side Panel  ${RESET}"
echo -e "${BOLD}${BLUE}====================================================${RESET}"

# Check for apt (Debian/Ubuntu)
if command -v apt-get >/dev/null 2>&1; then
    echo -e "\n${BOLD}[1/5] Checking and installing system dependencies...${RESET}"
    REQUIRED_PKGS=(
        "python3-nautilus"
        "gir1.2-gtksource-5"
        "gir1.2-webkit-6.0"
        "python3-markdown"
        "python3-pygments"
    )

    MISSING_PKGS=()
    for pkg in "${REQUIRED_PKGS[@]}"; do
        if ! dpkg -s "$pkg" >/dev/null 2>&1; then
            MISSING_PKGS+=("$pkg")
        fi
    done

    if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
        echo -e "${YELLOW}Installing missing packages: ${MISSING_PKGS[*]}${RESET}"
        sudo apt-get update -y
        sudo apt-get install -y "${MISSING_PKGS[@]}"
    else
        echo -e "${GREEN}✓ All required dependencies are already installed.${RESET}"
    fi
else
    echo -e "${YELLOW}Warning: Non-Debian/Ubuntu system detected. Ensure python-nautilus, gtksourceview-5, and webkit2gtk-6.0 are installed.${RESET}"
fi

# Define target paths
PREFIX="${HOME}/.local"
APP_DIR="${PREFIX}/share/nautilus-markdown-viewer"
EXT_DIR="${PREFIX}/share/nautilus-python/extensions"
ICON_DIR="${PREFIX}/share/icons/hicolor/scalable/actions"
DESKTOP_DIR="${PREFIX}/share/applications"
BIN_DIR="${PREFIX}/bin"
SCRIPTS_DIR="${PREFIX}/share/nautilus/scripts"

SCRIPT_SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "\n${BOLD}[2/5] Creating user installation directories...${RESET}"
mkdir -p "${APP_DIR}" "${EXT_DIR}" "${ICON_DIR}" "${DESKTOP_DIR}" "${BIN_DIR}" "${SCRIPTS_DIR}"

echo -e "\n${BOLD}[3/5] Installing application files...${RESET}"
# Copy viewer components
cp -r "${SCRIPT_SRC_DIR}/src/viewer/"* "${APP_DIR}/"
cp "${SCRIPT_SRC_DIR}/src/bin/markdown-preview" "${APP_DIR}/"
chmod +x "${APP_DIR}/markdown-preview" "${APP_DIR}/viewer.py"

# Symlink CLI binary
ln -sf "${APP_DIR}/markdown-preview" "${BIN_DIR}/markdown-preview"

# Install Nautilus Extension
cp "${SCRIPT_SRC_DIR}/src/extension/markdown_preview_extension.py" "${EXT_DIR}/"

# Install Icons
cp "${SCRIPT_SRC_DIR}/src/icons/text-markdown-symbolic.svg" "${ICON_DIR}/"
cp "${SCRIPT_SRC_DIR}/src/icons/text-markdown-symbolic.svg" "${ICON_DIR}/view-preview-symbolic.svg"

# Install Desktop file
cp "${SCRIPT_SRC_DIR}/src/desktop/io.github.markdown_previewer.desktop" "${DESKTOP_DIR}/"

# Install Nautilus script
cp "${SCRIPT_SRC_DIR}/scripts/Preview Markdown" "${SCRIPTS_DIR}/"
chmod +x "${SCRIPTS_DIR}/Preview Markdown"

echo -e "\n${BOLD}[4/5] Updating desktop and icon caches...${RESET}"
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -q "${PREFIX}/share/icons/hicolor/" 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true
fi

echo -e "\n${BOLD}[5/5] Reloading Nautilus File Explorer...${RESET}"
if command -v nautilus >/dev/null 2>&1; then
    nautilus -q 2>/dev/null || true
    echo -e "${GREEN}✓ Nautilus reloaded successfully.${RESET}"
fi

echo -e "\n${BOLD}${GREEN}====================================================${RESET}"
echo -e "${BOLD}${GREEN}  Installation Complete! 🎉                         ${RESET}"
echo -e "${BOLD}${GREEN}====================================================${RESET}"
echo -e "You can now:"
echo -e "  1. Open Nautilus and click the ${BOLD}M↓${RESET} icon in the top header bar to toggle the preview pane."
echo -e "  2. Right-click any Markdown file (.md) -> 'Preview Markdown'."
echo -e "  3. Launch from terminal: ${BOLD}markdown-preview <file.md>${RESET}"
echo -e "  4. Use ${BOLD}Ctrl + E${RESET} in the previewer to toggle into built-in ${BOLD}Editor Mode${RESET}!"

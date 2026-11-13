#!/usr/bin/env bash
# ==============================================================================
# Nautilus Markdown Viewer & Side Panel - Uninstallation Script
# ==============================================================================

set -e

BOLD="\033[1m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
RESET="\033[0m"

echo -e "${BOLD}Uninstalling Nautilus Markdown Viewer...${RESET}"

PREFIX="${HOME}/.local"
rm -rf "${PREFIX}/share/nautilus-markdown-viewer"
rm -f "${PREFIX}/share/nautilus-python/extensions/markdown_preview_extension.py"
rm -f "${PREFIX}/share/icons/hicolor/scalable/actions/text-markdown-symbolic.svg"
rm -f "${PREFIX}/share/icons/hicolor/scalable/actions/view-preview-symbolic.svg"
rm -f "${PREFIX}/share/applications/io.github.markdown_previewer.desktop"
rm -f "${PREFIX}/bin/markdown-preview"
rm -f "${PREFIX}/share/nautilus/scripts/Preview Markdown"

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -q "${PREFIX}/share/icons/hicolor/" 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${PREFIX}/share/applications" 2>/dev/null || true
fi

if command -v nautilus >/dev/null 2>&1; then
    nautilus -q 2>/dev/null || true
fi

echo -e "${GREEN}✓ Uninstallation complete. Nautilus has been reloaded.${RESET}"

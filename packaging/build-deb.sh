#!/usr/bin/env bash
# ==============================================================================
# Builds a standalone .deb package for Ubuntu / Debian
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build_deb/nautilus-markdown-viewer_1.0.0_all"
DEB_FILE="${SCRIPT_DIR}/nautilus-markdown-viewer_1.0.0_all.deb"

echo "Building Debian package for nautilus-markdown-viewer..."

rm -rf "${SCRIPT_DIR}/build_deb"
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/usr/share/nautilus-markdown-viewer"
mkdir -p "${BUILD_DIR}/usr/share/nautilus-python/extensions"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/scalable/actions"
mkdir -p "${BUILD_DIR}/usr/share/applications"
mkdir -p "${BUILD_DIR}/usr/bin"

# 1. Control file
cat << 'EOF' > "${BUILD_DIR}/DEBIAN/control"
Package: nautilus-markdown-viewer
Version: 1.0.0
Section: utils
Priority: optional
Architecture: all
Depends: python3 (>= 3.10), python3-nautilus, gir1.2-gtksource-5, gir1.2-webkit-6.0, python3-markdown, python3-pygments
Maintainer: Tuhin Das <dastuhin.rnj@gmail.com>
Homepage: https://github.com/whispererofenigma/nautilus-markdown-viewer
Description: Rich Markdown Viewer & Side Panel for Nautilus (GNOME Files)
 Integrates an embedded, horizontally draggable Markdown preview panel right
 inside Nautilus explorer, complete with live selection auto-display, hot-reload,
 in-app GtkSourceView 5 editor mode, and a standalone viewer window.
EOF

# 2. Post-installation script
cat << 'EOF' > "${BUILD_DIR}/DEBIAN/postinst"
#!/bin/sh
set -e
gtk-update-icon-cache -f -q /usr/share/icons/hicolor/ 2>/dev/null || true
update-desktop-database /usr/share/applications/ 2>/dev/null || true
exit 0
EOF
chmod 755 "${BUILD_DIR}/DEBIAN/postinst"

# 3. Post-removal script
cat << 'EOF' > "${BUILD_DIR}/DEBIAN/postrm"
#!/bin/sh
set -e
gtk-update-icon-cache -f -q /usr/share/icons/hicolor/ 2>/dev/null || true
update-desktop-database /usr/share/applications/ 2>/dev/null || true
exit 0
EOF
chmod 755 "${BUILD_DIR}/DEBIAN/postrm"

# 4. Copy payload files
cp -r "${SCRIPT_DIR}/src/viewer/"* "${BUILD_DIR}/usr/share/nautilus-markdown-viewer/"
cp "${SCRIPT_DIR}/src/bin/markdown-preview" "${BUILD_DIR}/usr/share/nautilus-markdown-viewer/"
chmod +x "${BUILD_DIR}/usr/share/nautilus-markdown-viewer/markdown-preview"
chmod +x "${BUILD_DIR}/usr/share/nautilus-markdown-viewer/viewer.py"

# Symlink executable to /usr/bin/markdown-preview
ln -sf /usr/share/nautilus-markdown-viewer/markdown-preview "${BUILD_DIR}/usr/bin/markdown-preview"

# Extension
cp "${SCRIPT_DIR}/src/extension/markdown_preview_extension.py" "${BUILD_DIR}/usr/share/nautilus-python/extensions/"

# Icons
cp "${SCRIPT_DIR}/src/icons/text-markdown-symbolic.svg" "${BUILD_DIR}/usr/share/icons/hicolor/scalable/actions/"
cp "${SCRIPT_DIR}/src/icons/text-markdown-symbolic.svg" "${BUILD_DIR}/usr/share/icons/hicolor/scalable/actions/view-preview-symbolic.svg"

# Desktop
cp "${SCRIPT_DIR}/src/desktop/io.github.markdown_previewer.desktop" "${BUILD_DIR}/usr/share/applications/"
sed -i 's|/home/whispererofenigma/.local/bin/|/usr/bin/|g' "${BUILD_DIR}/usr/share/applications/io.github.markdown_previewer.desktop"

# 5. Build package with dpkg-deb
dpkg-deb --build --root-owner-group "${BUILD_DIR}" "${DEB_FILE}"

echo "✓ Successfully built: ${DEB_FILE}"
rm -rf "${SCRIPT_DIR}/build_deb"

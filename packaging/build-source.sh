#!/usr/bin/env bash
# Build an unsigned source package from committed code for review or a PPA build.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(cat "${PROJECT_DIR}/VERSION")"
SERIES="${SERIES:-noble}"
REVISION="${REVISION:-1~ppa1}"
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || \
   [[ ! "$SERIES" =~ ^[a-z]+$ ]] || \
   [[ ! "$REVISION" =~ ^[0-9][a-zA-Z0-9.+~]*$ ]]; then
    echo "Invalid VERSION, SERIES, or REVISION." >&2
    exit 1
fi
if [[ -n "$(git -C "$PROJECT_DIR" status --porcelain --untracked-files=normal)" ]]; then
    echo "Commit the release files first; source packages use committed code only." >&2
    exit 1
fi

OUTPUT_DIR="${PROJECT_DIR}/dist/source"
mkdir -p "$OUTPUT_DIR"
SOURCE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/nautilus-markdown-source.XXXXXX")"
trap 'rm -rf "$SOURCE_DIR"' EXIT
SOURCE_NAME="nautilus-markdown-viewer-${VERSION}"
ARCHIVE_NAME="nautilus-markdown-viewer_${VERSION}.orig.tar.gz"
git -C "$PROJECT_DIR" archive --format=tar --prefix="${SOURCE_NAME}/" HEAD | \
    gzip -n > "${SOURCE_DIR}/${ARCHIVE_NAME}"
tar -xzf "${SOURCE_DIR}/${ARCHIVE_NAME}" -C "$SOURCE_DIR"
cp -a "${SOURCE_DIR}/${SOURCE_NAME}/packaging/debian" "${SOURCE_DIR}/${SOURCE_NAME}/debian"
cat > "${SOURCE_DIR}/${SOURCE_NAME}/debian/changelog" <<CHANGELOG
nautilus-markdown-viewer (${VERSION}-${REVISION}) ${SERIES}; urgency=medium

  * Package upstream release ${VERSION}.

 -- Tuhin Das <dastuhin.rnj@gmail.com>  $(date -R)
CHANGELOG
(
    cd "${SOURCE_DIR}/${SOURCE_NAME}"
    dpkg-source -b .
)
cp "${SOURCE_DIR}/"*.tar.* "${SOURCE_DIR}/"*.dsc "$OUTPUT_DIR/"
printf 'Unsigned source package: %s\n' "${OUTPUT_DIR}/nautilus-markdown-viewer_${VERSION}-${REVISION}.dsc"
printf 'Build and sign a source upload before submitting to Launchpad; see docs/distribution.md.\n'

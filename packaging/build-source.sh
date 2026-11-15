#!/usr/bin/env bash
# Build an Ubuntu source package from committed code for review or a PPA build.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(cat "${PROJECT_DIR}/VERSION")"
SERIES="${SERIES:-noble}"
REVISION="${REVISION:-1~ppa1}"
SIGN_KEY="${GPG_KEY:-}"

# Auto-detect default maintainer key if present in secret keys
DEFAULT_KEY="90A7D803B11BE7FAF9160AEC3236FA504F80451E"
if [[ -z "$SIGN_KEY" ]] && gpg --list-secret-keys "$DEFAULT_KEY" >/dev/null 2>&1; then
    SIGN_KEY="$DEFAULT_KEY"
fi

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

DSC_FILE="${SOURCE_DIR}/nautilus-markdown-viewer_${VERSION}-${REVISION}.dsc"
CHANGES_FILE="${SOURCE_DIR}/nautilus-markdown-viewer_${VERSION}-${REVISION}_source.changes"

if [[ -n "$SIGN_KEY" ]]; then
    echo "Signing source package with key: ${SIGN_KEY}"
    gpg --batch --no-tty --yes --clearsign -u "$SIGN_KEY" -o "${DSC_FILE}.signed" "$DSC_FILE"
    mv "${DSC_FILE}.signed" "$DSC_FILE"

    (
        cd "${SOURCE_DIR}/${SOURCE_NAME}"
        dpkg-genchanges -S -sa "-O${CHANGES_FILE}"
    )
    gpg --batch --no-tty --yes --clearsign -u "$SIGN_KEY" -o "${CHANGES_FILE}.signed" "$CHANGES_FILE"
    mv "${CHANGES_FILE}.signed" "$CHANGES_FILE"

    cp "${SOURCE_DIR}/"*.tar.* "${DSC_FILE}" "${CHANGES_FILE}" "$OUTPUT_DIR/"
    printf 'Signed source package generated in: %s\n' "$OUTPUT_DIR"
    printf '  DSC: %s\n' "${OUTPUT_DIR}/$(basename "$DSC_FILE")"
    printf '  Changes: %s\n' "${OUTPUT_DIR}/$(basename "$CHANGES_FILE")"
    printf 'Upload to Launchpad using:\n'
    printf '  dput ppa:whispererofenigma/<ppa-name> %s\n' "${OUTPUT_DIR}/$(basename "$CHANGES_FILE")"
else
    (
        cd "${SOURCE_DIR}/${SOURCE_NAME}"
        dpkg-genchanges -S -sa "-O${CHANGES_FILE}"
    )
    cp "${SOURCE_DIR}/"*.tar.* "${DSC_FILE}" "${CHANGES_FILE}" "$OUTPUT_DIR/"
    printf 'Unsigned source package: %s\n' "${OUTPUT_DIR}/nautilus-markdown-viewer_${VERSION}-${REVISION}.dsc"
    printf 'Sign the .dsc and _source.changes before submitting to Launchpad; see docs/distribution.md.\n'
fi

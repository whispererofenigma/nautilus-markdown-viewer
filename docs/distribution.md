# Distribution

## Available channel

[GitHub Releases](https://github.com/whispererofenigma/nautilus-markdown-viewer/releases)
provide source snapshots and native `.deb` packages. Starting with 1.1.0, releases
include SHA-256 checksums and are gated by the reusable CI workflow. Checksums
verify download consistency; they are not an independent publisher signature.

The application ships AppStream metadata and a desktop entry for Linux software
catalogs. Metadata alone does not enroll the project in a store or repository.
The native package is the primary distribution format because the extension loads
inside the host Nautilus process.

## Ubuntu PPA preparation

No official project PPA is published yet. The repository includes Debian source
packaging for a maintainer to build, sign, and upload to Launchpad.

### Automated source package and signature

If you have your registered OpenPGP secret key in your GPG keyring, `packaging/build-source.sh`
automatically signs both the `.dsc` and `_source.changes` with your key:

```sh
# Generate and sign the source package for Ubuntu 24.04 (noble)
bash packaging/build-source.sh
```

The signed `.dsc`, `.orig.tar.gz`, `.debian.tar.xz`, and `_source.changes` are written
to `dist/source/`. The default target is Ubuntu 24.04 (`noble`), revision `1~ppa1`.
Use a new revision for every upload, for example `REVISION=1~ppa2 bash packaging/build-source.sh`.
To target a different series (e.g. `oracular` or `jammy`), specify `SERIES=<name>`.

### Uploading to Launchpad

1. Activate your PPA on Launchpad at `https://launchpad.net/~<username>/+activate-ppa`.
2. Install `dput`:
   ```sh
   sudo apt install dput
   ```
3. Upload the signed changes file:
   ```sh
   dput ppa:<username>/<ppa-name> dist/source/nautilus-markdown-viewer_1.1.0-1~ppa1_source.changes
   ```

Launchpad will verify your OpenPGP signature against your registered Launchpad key,
accept the upload into its build queue, and automatically build the binary `.deb`
package for the targeted Ubuntu architecture(s).

### Manual build alternative

You can also inspect, extract, and build manually using standard Debian tooling:

```sh
dpkg-source -x dist/source/nautilus-markdown-viewer_1.1.0-1~ppa1.dsc
cd nautilus-markdown-viewer-1.1.0
debuild -S -sa -kYOUR_REGISTERED_KEY_FINGERPRINT
```

## Other distribution formats

A Flatpak may be useful for the **standalone viewer**. It needs a separate manifest,
sandbox and file-access testing, bundled runtime dependencies, screenshots, and
AppStream/store validation. A sandboxed viewer does not by itself install a Python
extension into the host Nautilus process. This separation follows Flatpak's
[runtime and filesystem model](https://docs.flatpak.org/en/latest/conventions.html).
Follow the current [Flathub submission process](https://docs.flathub.org/docs/for-app-authors/submission)
after a local build and runtime check. No Flatpak or Flathub listing is supplied here.

Distribution repositories such as Debian or Fedora require their own packaging,
review, and ongoing maintenance. Prefer a small number of tested channels over
unverified manifests for every package manager. GNOME Shell's extension directory
is not a distribution channel for Nautilus Python extensions.

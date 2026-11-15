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
packaging for a maintainer to build, review, and upload. Use a clean committed
checkout and install the packaging tools:

```sh
sudo apt install build-essential debhelper dh-python devscripts dpkg-dev \
  python3-markdown python3-pygments
bash packaging/build-source.sh
```

The unsigned `.dsc`, original source archive, and Debian archive are written to
`dist/source/`. The default target is Ubuntu 24.04 (`noble`), revision `1~ppa1`.
Use a new revision for every upload, for example `REVISION=1~ppa2`. Do not claim
support for a new distribution until its dependency resolution and desktop runtime
have been tested.

Before upload, extract and build the source package in an appropriate clean Ubuntu
build environment (for example sbuild). Smoke-test the resulting binary package in
a fresh desktop account. To prepare the signed source upload after those checks:

```sh
# Run in a separate temporary working directory; adjust the path to your checkout.
dpkg-source -x /path/to/checkout/dist/source/nautilus-markdown-viewer_1.1.0-1~ppa1.dsc
cd nautilus-markdown-viewer-1.1.0
debuild -S -sa -kYOUR_REGISTERED_KEY_FINGERPRINT
# Upload the generated *_source.changes with dput to your activated PPA.
```

Launchpad requires an account, an activated PPA, and an associated OpenPGP key.
Never commit private signing keys. Follow the official
[source-package upload guide](https://ubuntu.com/docs/launchpad/user/how-to/packaging/build-deb-packages-in-launchpad/)
for signing and the exact `dput` destination. A source archive is not proof of a
successful Launchpad build; publish installation instructions only after it succeeds.

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

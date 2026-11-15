# Nautilus Markdown Viewer

[![CI](https://github.com/whispererofenigma/nautilus-markdown-viewer/actions/workflows/ci.yml/badge.svg)](https://github.com/whispererofenigma/nautilus-markdown-viewer/actions/workflows/ci.yml)
[![Ubuntu PPA](https://img.shields.io/badge/Ubuntu%20PPA-nautilus--markdown--viewer-orange.svg)](https://launchpad.net/~whispererofenigma/+archive/ubuntu/nautilus-markdown-viewer)
[![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)

Preview and edit Markdown in GNOME Files. Nautilus Markdown Viewer adds a
resizable preview pane to Nautilus and a standalone GTK 4 / Libadwaita viewer.
Select a document to read it alongside your files, or open it in its own window.

## Features

- **Rich preview:** headings, tables, checklists, blockquotes, GitHub-style alerts,
  images, syntax-highlighted code with copy buttons, and MathJax equations.
- **Embedded side pane:** follows the selected Markdown file, resizes with a
  draggable divider, and opens documents in a separate window when needed.
- **Built-in editor:** GtkSourceView syntax highlighting, line numbers, word wrap,
  and in-place saving. External changes are checked before a save overwrites disk.
- **Live updates:** monitors the open document for changes, including atomic saves
  made by other editors.
- **Reading tools:** per-document scroll memory and a reading-progress indicator.
  The standalone viewer also offers search, a table of contents, zoom, and a
  light/dark/system theme selector.
- **Desktop integration:** a Nautilus context-menu action, command-line launcher,
  and shortcuts to external editors.

The side pane keeps a WebKit document alive between selections, renders Markdown
in the background, and caches recent documents. A delayed loading indicator gives
feedback when a selection takes longer to display. Performance depends on document
size, media, hardware, and browser initialization; no fixed latency is guaranteed.

## Requirements and compatibility

The tested environment is **Ubuntu 24.04 with Nautilus 46.4**. Required components:

| Component | Requirement |
| --- | --- |
| Python | 3.10 or newer, with PyGObject |
| Desktop | GTK 4 and Libadwaita 1 |
| Preview | WebKitGTK 6.0 introspection bindings |
| Editor | GtkSourceView 5 introspection bindings |
| Nautilus integration | Nautilus 4.0 Python extension API |
| Markdown conversion | Python-Markdown and Pygments |

The side pane uses Nautilus's internal widget structure, which can change between
versions. Other GNOME releases need compatibility testing. The standalone viewer
and context-menu action do not depend on that pane layout. Ubuntu 22.04 is not a
supported installation target with its default package set.

## Installation

Choose **one** installation method. A user installation can shadow a system
package; remove the user installation before switching to the system package.

### Ubuntu PPA (Recommended)

Automatic installation and updates for Ubuntu 24.04 LTS and compatible distributions:

```sh
sudo add-apt-repository ppa:whispererofenigma/nautilus-markdown-viewer
sudo apt update
sudo apt install nautilus-markdown-viewer
nautilus -q
```

### Standalone Debian / Ubuntu package (.deb)

Download the `.deb` and `SHA256SUMS` from a [release](https://github.com/whispererofenigma/nautilus-markdown-viewer/releases).
For releases that include checksums, place both files in the same directory and
verify them before installing:

```sh
sha256sum --check SHA256SUMS
sudo apt install ./nautilus-markdown-viewer_1.1.0_all.deb
nautilus -q
```

Use the filename for the version you downloaded. Reopen Files after installation.
Quitting Nautilus closes its existing windows. Dependencies must be available in
your distribution; this is not a self-contained application bundle.

### User installation from source

```sh
git clone https://github.com/whispererofenigma/nautilus-markdown-viewer.git
cd nautilus-markdown-viewer
# Optional: git checkout v1.1.0 to use that release instead of main.
bash install.sh
```

The installer copies the application to `~/.local/share/nautilus-markdown-viewer`,
adds a launcher in `~/.local/bin`, installs the Nautilus extension for your user,
and quits Nautilus so the extension can reload. On apt-based distributions it
requests sudo only if dependencies are missing. Add `~/.local/bin` to your PATH
if the terminal cannot find `markdown-preview`.

### Updates and removal

- **PPA users:** updates arrive automatically with normal system updates:
  ```sh
  sudo apt update && sudo apt upgrade
  ```
- **Manual package users:** download and install the newer release with `sudo apt install ./<package>.deb`.
- **Source users:** update your checkout and rerun `bash install.sh`.

To remove the system package:

```sh
sudo apt remove nautilus-markdown-viewer
nautilus -q
```

To remove the Launchpad PPA:

```sh
sudo add-apt-repository --remove ppa:whispererofenigma/nautilus-markdown-viewer
```

For a source installation, run `bash uninstall.sh` from the checkout to remove the user installation.
Neither uninstall method removes your Markdown documents.

## Usage

In Files, click **M↓** in the header bar and select a Markdown document. Drag the
divider to adjust the pane width. Use its toolbar to edit, save, reload, open an
external editor, or pop out the document.

For a separate window, right-click a Markdown file and choose **Preview Markdown**,
or run:

```sh
markdown-preview /path/to/document.md
```

The panel saves edits before changing files or closing. If saving fails or an
external edit is detected, it keeps the editor buffer open. The standalone viewer
asks before discarding unsaved changes.

| Shortcut | Action | Available in |
| --- | --- | --- |
| Ctrl+E | Switch preview/editor | Pane and standalone |
| Ctrl+S | Save edits | Pane and standalone |
| Ctrl+F / Esc | Open / close search | Standalone |
| Enter / Shift+Enter | Next / previous search result | Standalone search |
| Ctrl++ / Ctrl+- / Ctrl+0 | Zoom in / out / reset | Standalone |
| Ctrl+R / F5 | Reload | Standalone |
| Ctrl+W / Ctrl+Q | Close window | Standalone |

## Limitations and troubleshooting

- MathJax is downloaded when a document contains equations. Remote images and math
  therefore need a network connection; ordinary Markdown and local images work offline.
- Raw HTML is supported. This viewer is not designed as an isolation boundary for
  untrusted documents; embedded resources can contact external servers.
- MDX and R Markdown are shown as Markdown; JSX and R code are not executed.
- Monitoring a symlink target in another directory is not supported.
- If the pane button is missing, restart Nautilus and check the installed Nautilus
  and `python3-nautilus` versions. Include those versions in a bug report.
- If rendering is slow, include the document size and whether the delay happens
  only on first selection. See the [performance notes](docs/performance-and-validation.md)
  for measurement details and the embedded view's acceleration override.

## Development and contributing

Bug reports, documentation improvements, compatibility reports, and focused pull
requests are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) for setup and checks.
Use [GitHub Issues](https://github.com/whispererofenigma/nautilus-markdown-viewer/issues)
for reproducible bugs and feature proposals. For sensitive reports, see
[SECURITY.md](SECURITY.md).

```sh
make test PYTHON=/usr/bin/python3
make test-desktop PYTHON=/usr/bin/python3  # Requires a graphical session
bash packaging/build-deb.sh
```

The source is organized into `src/viewer` (GTK UI and Markdown rendering),
`src/extension` (Nautilus integration), `tests`, and `packaging`.
See the [changelog](CHANGELOG.md), [release guide](docs/releasing.md), and
[distribution guide](docs/distribution.md).

## License

Copyright © 2026 Tuhin Das and contributors. Distributed under the
[GNU General Public License, version 3](LICENSE). Dependencies retain their
respective licenses.

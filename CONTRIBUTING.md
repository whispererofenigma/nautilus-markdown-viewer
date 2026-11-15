# Contributing

Thank you for helping improve Nautilus Markdown Viewer. Small, focused changes,
clear bug reports, and testing on additional GNOME releases are useful contributions.
Please keep discussions respectful and critique ideas and code rather than people.

## Report a problem or propose a feature

Search existing issues first. For bugs, include your distribution, Nautilus version,
WebKitGTK version, installation method, steps to reproduce, and expected versus
actual behavior. Attach a minimal Markdown example with private information removed.
For performance reports, distinguish first selection from repeated selection and
include document size and external resources.

Discuss large architectural changes or new dependencies in an issue before investing
in an implementation. Do not post credentials or private documents in public issues;
use the process in [SECURITY.md](SECURITY.md) for vulnerabilities.

## Development environment

On Ubuntu 24.04:

```sh
sudo apt install python3-gi python3-nautilus gir1.2-gtk-4.0 gir1.2-adw-1 \
  gir1.2-gtksource-5 gir1.2-webkit-6.0 python3-markdown python3-pygments \
  python3-venv desktop-file-utils appstream
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements-dev.txt
```

Run the standalone application from the checkout:

```sh
./src/bin/markdown-preview README.md
```

To test the embedded pane, run `bash install.sh`, then reopen Nautilus. This installs
working-tree files for your user and closes existing Nautilus windows. Rerun the
installer after changing code; editing the checkout does not update installed copies.
For extension diagnostics, quit Nautilus and start it in a terminal:

```sh
nautilus -q
NAUTILUS_PYTHON_DEBUG=misc nautilus
```

## Checks before opening a pull request

```sh
.venv/bin/black --check src/viewer src/extension tests
make test PYTHON=/usr/bin/python3
make test-desktop PYTHON=/usr/bin/python3
bash -n install.sh uninstall.sh packaging/build-deb.sh
desktop-file-validate src/desktop/io.github.markdown_previewer.desktop
appstreamcli validate --no-net src/metainfo/io.github.markdown_previewer.metainfo.xml
bash packaging/build-deb.sh
git diff --check
```

Desktop tests need a graphical session, GTK, and WebKit. Headless CI runs them with
Xvfb and a session bus. The core suite skips desktop checks unless explicitly enabled.
Tests should check observable behavior and wait for state transitions with bounded
deadlines. Add a regression test when it meaningfully protects a fix. For integration
changes, also check real Nautilus selection, resizing, tabs, and editor save behavior.

Use four-space Python indentation and Black formatting. Keep UI construction,
rendering, background work, and persistence responsibilities separate. Avoid blocking
file operations on the GTK event loop. Explain non-obvious compatibility choices.

## Pull request workflow

1. Fork the project if needed and create a descriptive branch from current `main`.
2. Keep commits focused; use concise, imperative messages that explain the change.
3. Update user documentation and the Unreleased changelog for user-visible changes.
4. Run relevant checks and describe what passed, what was not tested, and why.
5. Open a pull request explaining the problem and resulting behavior; link related
   issues and include screenshots for visual changes when practical.
6. Address review feedback and wait for CI before merging. Do not force-push shared
   branches or include generated packages, caches, credentials, or personal notes.

Contributions are distributed under this repository's GPL-3.0 license. Only submit
work you have the right to contribute. No contributor license agreement is required.
Maintainers do not promise a response deadline; concise reproductions help triage.

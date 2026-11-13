# Nautilus Markdown Viewer & Side Panel

<p align="center">
  <img src="src/icons/text-markdown-symbolic.svg" width="96" height="96" alt="Markdown Logo" />
</p>

<p align="center">
  <b>A native, modern GNOME / Libadwaita Markdown previewer and embedded, horizontally resizable side panel for Nautilus (GNOME Files).</b>
</p>

<p align="center">
  <a href="https://github.com/whispererofenigma/nautilus-markdown-viewer/actions"><img src="https://img.shields.io/badge/CI-Passing-brightgreen?style=flat-square" alt="CI Status" /></a>
  <a href="https://ubuntu.com"><img src="https://img.shields.io/badge/Ubuntu-24.04%20%7C%2022.04-E95420?style=flat-square&logo=ubuntu" alt="Ubuntu" /></a>
  <a href="https://www.gnome.org"><img src="https://img.shields.io/badge/GNOME-42%20--%2046-4a86cf?style=flat-square&logo=gnome" alt="GNOME" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-GPL--3.0-blue?style=flat-square" alt="License" /></a>
</p>

---

## ✨ Features

- 📑 **Embedded Nautilus Side Panel**:
  - Toggled directly via a header bar **`M↓`** button in Nautilus File Explorer.
  - **Horizontally draggable & stretchable** splitter (`Gtk.Paned`) with customizable width.
  - **Live Explorer Selection Tracking**: Click or arrow-key to any `.md` file in Nautilus and it renders instantly!
- ⚡ **Built-In Editor Mode (`GtkSourceView 5`)**:
  - Switch between **Preview Mode** and **Editor Mode** with **`Ctrl + E`**.
  - Syntax highlighting, line numbers, word wrap, and **`Ctrl + S`** in-place saving.
- 🪟 **Standalone Libadwaita Viewer Window**:
  - Launch from right-click context menu, terminal (`markdown-preview <file.md>`), or panel pop-out.
- 🌓 **Dynamic Dark / Light Themes**:
  - Automatically syncs with GNOME system color scheme in real-time.
  - Manual theme switcher (Auto / Dark / Light).
- 🧭 **Interactive Navigation**:
  - Table of Contents popover with smooth-scrolling anchors.
  - In-page Find (`Ctrl + F`) with match count and navigation.
- 📋 **GitHub-Flavored Markdown**:
  - Code syntax highlighting (Pygments) with language badges and **One-Click Copy**.
  - GitHub Alerts (`> [!NOTE]`, `> [!TIP]`, `> [!WARNING]`, etc.) with vector icons.
  - Math & LaTeX equations rendered via MathJax.
  - Checklists (`- [x]`, `- [ ]`), tables, and blockquotes.
- 🔄 **Inotify Live Hot-Reload**:
  - Automatically re-renders when the file is modified and saved in external editors, preserving scroll position.
- 🛠️ **External Editor Integration**:
  - Launch VS Code or GNOME Text Editor directly without duplicate preview windows.

---

## 🚀 Quick Install

### Method 1: Automated One-Line Installer (Recommended)

```bash
curl -sSL https://raw.githubusercontent.com/whispererofenigma/nautilus-markdown-viewer/main/install.sh | bash
```

### Method 2: Ubuntu / Debian Package (`.deb`)

Download the latest `.deb` from [Releases](https://github.com/whispererofenigma/nautilus-markdown-viewer/releases) or build it locally:

```bash
sudo apt install ./nautilus-markdown-viewer_1.0.0_all.deb
```

### Method 3: From Source (Developers)

```bash
git clone https://github.com/whispererofenigma/nautilus-markdown-viewer.git
cd nautilus-markdown-viewer
chmod +x install.sh
./install.sh
```

---

## 🖥️ Compatibility

| Platform / Component | Supported Versions | Notes |
| :--- | :--- | :--- |
| **Ubuntu** | 24.04 LTS (Noble), 22.04 LTS (Jammy) | Fully verified with default AppArmor profiles |
| **GNOME Files (Nautilus)**| Nautilus 43, 44, 45, 46 | GTK4 + Libadwaita architecture |
| **Python** | 3.10, 3.11, 3.12+ | Uses `python3-nautilus` 4.0 bindings |
| **WebKitGTK** | WebKitGTK 6.0 | Hardware-accelerated rendering |
| **Editor Backend** | GtkSourceView 5 | Native syntax-highlighted editor |

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Description |
| :--- | :--- |
| **`Ctrl + E`** | Toggle between **Preview Mode** and **Editor Mode** |
| **`Ctrl + S`** | Save changes in Editor Mode |
| **`Ctrl + F`** / **`Esc`** | Open / Close Search Bar |
| **`Enter`** / **`Shift + Enter`** | Next / Previous Search Match |
| **`Ctrl + +`** / **`Ctrl + -`** | Zoom In / Zoom Out |
| **`Ctrl + 0`** | Reset Zoom (100%) |
| **`Ctrl + R`** or **`F5`** | Force Reload Document |
| **`Ctrl + W`** / **`Ctrl + Q`** | Close Window |

---

## 📦 Project Structure

```text
nautilus-markdown-viewer/
├── src/
│   ├── extension/
│   │   └── markdown_preview_extension.py   # Nautilus 4.0 Python extension hook
│   ├── viewer/
│   │   ├── viewer.py                       # Standalone Libadwaita window
│   │   ├── panel.py                        # Embedded Nautilus side panel
│   │   ├── renderer.py                     # Markdown to HTML rendering engine
│   │   └── styles.py                       # GitHub Light & Dark CSS themes
│   ├── bin/
│   │   └── markdown-preview                # CLI wrapper script
│   ├── icons/
│   │   └── text-markdown-symbolic.svg      # Official vector Markdown logo
│   └── desktop/
│       └── io.github.markdown_previewer.desktop
├── packaging/
│   ├── debian/                             # Debian packaging controls
│   └── build-deb.sh                        # .deb builder script
├── install.sh                              # Automatic setup script
├── uninstall.sh                            # Clean uninstallation script
├── Makefile
├── LICENSE                                 # GNU General Public License v3
└── README.md
```

---

## 🗑️ Uninstallation

To cleanly remove the extension, viewer, and desktop integrations:

```bash
curl -sSL https://raw.githubusercontent.com/whispererofenigma/nautilus-markdown-viewer/main/uninstall.sh | bash
```
Or from the cloned repository:
```bash
./uninstall.sh
```

---

## 📄 License

Distributed under the **GNU General Public License v3 (GPL-3.0)**. See [`LICENSE`](LICENSE) for details.

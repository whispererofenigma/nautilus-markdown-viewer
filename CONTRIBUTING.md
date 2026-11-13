# Contributing to Nautilus Markdown Viewer

We welcome contributions from users and open-source developers!

## Development Setup

1. Clone the repository:
   ```bash
   git clone git@github.com:whispererofenigma/nautilus-markdown-viewer.git
   cd nautilus-markdown-viewer
   ```

2. Install system dependencies:
   ```bash
   sudo apt install -y python3-nautilus gir1.2-gtksource-5 gir1.2-webkit-6.0 python3-markdown python3-pygments
   ```

3. Install in user mode for testing:
   ```bash
   ./install.sh
   ```

4. Debugging Nautilus Extensions:
   Run Nautilus with debug logging:
   ```bash
   nautilus -q
   NAUTILUS_PYTHON_DEBUG=misc nautilus
   ```

5. Building a `.deb` package:
   ```bash
   ./packaging/build-deb.sh
   ```

6. Submit a Pull Request:
   Ensure your Python code compiles without warnings (`make test`).

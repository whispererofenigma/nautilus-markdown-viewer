# Performance and feature review

## Rich preview architecture

The panel uses rich HTML preview. WebKit starts when the panel is constructed and keeps
one document alive. File selection replaces only the Markdown content fragment;
it does not reload styles, scripts or the browser document.

Background rendering, stale-result cancellation, an eight-document / 8 MiB LRU
cache and cached GTK selection models reduce work on each selection. File content
is rechecked before using cached HTML. Fontconfig resolves installed fonts once;
explicit local font faces and prewarming reduce browser fallback matching. Long
font-family chains were removed. Later blocks defer layout with CSS
content-visibility; math, images and SVG-containing blocks are excluded.

The embedded WebKit view defaults to software rendering after local comparisons
on the measured Ivy Bridge machine. To compare other hardware, start Nautilus with
MARKDOWN_PREVIEW_ACCELERATION=always, never, or default in its environment after
quitting the existing process. This changes only the embedded WebKit setting,
not the system GTK renderer. Missing local fonts fall back to generic fonts.

A GTK spinner appears after 100 ms and disappears after the current revision
reports two browser animation-frame callbacks. Stale completions cannot dismiss
another selection's loader. Errors clear the loader; a 15-second browser deadline
provides a recoverable error instead of spinning indefinitely. Remote images and
MathJax may continue loading after the document's initial frame.

## Research and measured decisions

An upstream [WebKitGTK font-matching issue](https://bugs.webkit.org/show_bug.cgi?id=315135)
reports expensive repeated Fontconfig matching. Local font-family experiments
also showed substantial cost here; this does not prove that every delay has the
same upstream cause. The measured environment used WebKit 2.52.6.

[WebKit settings](https://api.pygobject.gnome.org/WebKit-6.0/class-Settings.html)
provide the per-view hardware acceleration policy used in the comparison.
[CSS containment](https://www.w3.org/TR/css-contain-2/) allows off-screen layout
work to be deferred. Because upstream reports describe
[content-visibility rendering problems](https://bugs.webkit.org/show_bug.cgi?id=321501),
we exclude complex media blocks and verify off-screen find and heading navigation.

A language rewrite would not remove the measured browser font/layout costs.
Keeping WebKit retains rich HTML, search, images and math while addressing those
costs directly. This is a measured implementation choice, not a claim that no
further optimization is possible.

## Measurements

Sequential standalone panel experiments used CONTRIBUTING.md and README.md.
With persistent rich rendering but long font fallback chains, first-document
updates took roughly 675 / 1,682 ms to apply and 1,314 / 1,935 ms through two
subsequent browser frames. Local fonts, fragment replacement, prewarming and
deferred layout reduced isolated cold samples to roughly 78 / 163 ms applied
and 139 / 515 ms through frames. Runs varied under desktop load.

A final installed Nautilus 46.4 run exercised its actual GTK selection model:

| Selection | DOM applied | Through two subsequent browser frames |
| --- | ---: | ---: |
| First CONTRIBUTING.md | 136 ms | 174 ms |
| First README.md | 259 ms | 725 ms |
| Eight repeat selections | 17–88 ms | 64–188 ms |

“Cold” here means first selection of each file in a fresh process with the panel
already initialized; it is not total Nautilus launch time. Frame callbacks are a
scheduling proxy, not an optical display measurement. README includes remote
assets; its content also evolved during development. These are observed local
samples, not a controlled cross-machine benchmark or a universal 100 ms guarantee.
Browser rasterization, large documents, remote assets and math remain variable.

Python conversion of a separate twelve-unlabelled-fence workload improved from
a median 243.8 ms to 13.8 ms over three runs by disabling language guessing.
That result measures conversion only, not browser presentation.

Profiling used temporary instrumentation that is not included in release builds.

## Implementation notes

1. **Remove avoidable rendering work.** Disable Pygments language guessing for
   unlabelled fences, cache stylesheet generation, load MathJax only for documents
   containing math delimiters, and debounce scroll persistence.
2. **Keep GTK responsive.** Read and render in a single worker per preview. Cancel
   queued requests when newer selections arrive, reject stale results on the GTK
   thread, and reuse the last rendered document when its text has not changed.
   Closing a view cancels pending delivery and shuts down its worker.
3. **Fix existing behavior.** Preserve formatted heading titles, code-language
   badges, alert formatting, literal code examples, and TeX delimiters. Apply
   themes after page load. Handle F5 and Shift+Enter, escape paths and JavaScript
   arguments, and monitor directories to detect atomic file replacement.
4. **Protect editing.** Use atomic writes, retain permissions and symlinks, detect
   external edits before saving, keep the editor open after save failure, and ask
   before discarding standalone edits. The panel saves before changing selections
   or closing; save failures keep its current document open.
5. **Add focused improvements.** Show a reading-progress strip, maintain separate
   scroll positions for sibling files, respect reduced-motion preferences, and
   support the panel's advertised Ctrl+E / Ctrl+S shortcuts.
6. **Reduce integration overhead.** Skip view discovery while the Nautilus panel
   is hidden, connect public GTK selection models, remove handlers for retired
   views, and release window resources. Fix user/system install paths and the
   source-tree launcher.

## Repeatable checks

```sh
make test PYTHON=/usr/bin/python3
make test-desktop PYTHON=/usr/bin/python3
```

The first command checks syntax and runs the portable renderer/file-integrity
suite. Desktop tests are explicitly skipped unless enabled. The second command
runs the entire suite with actual GTK, GtkSourceView, WebKit and a display server.
It creates temporary documents and application windows; it does not alter the
installed Nautilus extension. Desktop checks wait for actual state transitions
with bounded deadlines.

| Feature | Verification coverage |
| --- | --- |
| Headings, duplicate anchors, formatted TOC | Renderer assertions and WebKit DOM |
| Code highlighting, language badges, literal code examples | Renderer assertions |
| Checklists, alerts, tables, reading metrics | Renderer assertions |
| Math | Delimiter preservation and conditional script loading; CDN typesetting requires a network check |
| Standalone preview and editor | Live GTK mode transitions and file-content assertions |
| Save, external-edit conflicts, symlinks, permissions | File-integrity and live editor checks |
| Theme cycle and zoom/reset | WebKit DOM and zoom-level assertions |
| Find and Escape | Real WebKit match-count callback and GTK search state |
| Atomic-save hot reload and F5 | Live file monitor and shortcut handler |
| Panel selection, editing and Ctrl+E | Real panel widget and temporary files |
| Rapid selections and missing files | Background-loader delivery/error checks |
| Relative images, clipboard button, scroll restoration, progress | Live WebKit checks |
| Nautilus header injection, splitter and actual icon/list selection | Live Nautilus 46 icon-view selection exercised; other versions/list view still need smoke testing |
| External editor launch, browser/email links, pop-out | Code reviewed; external application dispatch not exercised |
| Desktop installation and package payload | Shell syntax and package build checks |

The desktop suite calls widget methods and checks their actual results; it is not
an exhaustive physical keyboard/mouse test. Closing with unsaved edits and
Shift+Enter should also be included in a manual release smoke test. Nautilus uses
private widget structure for panel insertion, so support across versions must not
be inferred from the standalone suite. Unsupported toolbar layouts leave the
context-menu viewer available.

Rich-only panel regression checks cover correct base URLs, content changes, cache
revisits, no full-page navigation during selection changes, delayed loading and
error recovery, frame completion, off-screen search, and heading navigation.

## Release smoke checklist

- Install on the target GNOME system, restart Nautilus, and toggle the panel.
- Drag its divider; select files in icon and list views; switch tabs/folders.
- Edit in the panel, select another file, and confirm the saved content.
- Verify panel close, Nautilus close, and standalone Save/Discard/Cancel behavior.
- Exercise TOC navigation, Enter/Shift+Enter, external links and editor launch.
- Open a math document with network access and confirm visible typesetting.

## Deliberate limits

MathJax remains CDN-backed. MDX/R Markdown extensions preview ordinary Markdown;
this application does not execute JSX or R. A conflict preserves the editor buffer
and refuses to overwrite disk; there is no automatic merge UI. Monitoring a
symlink's *target* when it changes in a different directory remains unsupported.
Raw HTML remains supported as before; these changes are not an HTML-sanitization
or WebKit-sandbox audit.

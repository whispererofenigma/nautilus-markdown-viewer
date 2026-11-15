# Release procedure

1. Start from current `main` on a release branch. Review the changelog, open issues,
   compatibility claims, and any upgrade notes.
2. Update `VERSION`, the changelog, AppStream release metadata, README installation
   examples, and `docs/releases/v<version>.md`. Use a new version; never move an
   existing published tag.
3. Run the contribution checks, build the `.deb`, inspect its contents, and test
   installation and removal in an appropriate desktop environment. Ensure a user
   copy does not shadow the system package during validation.
4. Open a pull request. Review its diff and wait for both CI jobs, including the
   GTK/WebKit tests. Merge without rewriting shared branch history.
5. Tag the merged commit with an annotated `v<version>` tag and push that tag.
   Sign it if a maintainer signing key is configured; do not imply an unsigned tag
   is cryptographically authenticated.
6. The release workflow reruns CI, verifies the tag matches `VERSION`, downloads
   the package built by those checks, verifies checksums, and publishes release
   notes and assets. Inspect the finished release and verify downloaded checksums.
7. Keep failed releases unpublished until corrected. Do not replace published
   artifacts silently; issue a new version for corrections.
8. Build and test distribution-specific source packages separately. Announce only
   channels that actually have a successful, installable release.

The core tests do not replace a graphical desktop check. The test suite also does
not establish compatibility with every Nautilus version, which uses private widget
structure for pane insertion. See the release smoke checklist in the
[validation notes](performance-and-validation.md).

# Changelog

All notable changes to this project are documented in this file.

The project uses tagged releases. Each release entry should be kept in sync
with the corresponding Git tag and GitHub Release page.

## Unreleased

### Added

- Initial release workflow with tag-based installs from GitHub Releases.
- Public Klever package layout with `pyproject.toml`, `scripts/check-playlist`,
  and `scripts/install.sh`.
- Environment-driven configuration for playlist ID, runtime directory,
  transcript languages, and optional analysis context files.

### Changed

- Removed life-specific assumptions from the public code path.
- Analysis prompts now read optional context files instead of hard-coded
  ecosystem documents.

## v0.1.0 - 2026-07-06

### Added

- Public open-source YouTube playlist watcher repository.
- Playlist scan flow that pulls metadata from `yt-dlp`.
- Transcript fetch support through `youtube-transcript-api`.
- Pending queue, transcript cache, analysis archive, and runtime memory files
  under `data/`.
- CLI entrypoint and shell wrapper for quick checks and full scans.
- GitHub Actions release workflow triggered by semantic tags.
- Installer for fetching a tagged release into a local virtual environment.

### Security

- Repository uses an MIT license.
- Runtime state is kept outside version control.
- Installer blocks unsafe tar archive extraction paths.


# ke-youtube-playlist-watcher

Watcher for a public YouTube playlist. It scans for new videos, fetches
metadata and transcripts, stores a queue of pending items, and generates a
structured analysis report for each video.

## What it does

- Polls a YouTube playlist for new uploads.
- Fetches metadata with `yt-dlp`.
- Fetches transcripts with `youtube-transcript-api`.
- Caches pending videos, transcripts, and analysis results under `data/`.
- Builds a structured analysis prompt that can include optional context files.

## Quick start

```bash
cp .env.example .env
./scripts/check-playlist
```

## Configuration

Set the playlist and any optional context files through environment variables:

- `YTW_PLAYLIST_ID` - required playlist id.
- `YTW_PLAYLIST_TITLE` - display name for logs and memory output.
- `YTW_CONTEXT_FILES` - optional `:`-separated list of context files.
- `YTW_DATA_DIR` - override the runtime state directory.
- `YTW_TRANSCRIPT_LANGUAGES` - comma-separated language preference list.

## Release installs

Install from a tagged release:

```bash
./scripts/install.sh --version latest
```

Or install a specific tag:

```bash
./scripts/install.sh --version v0.1.0
```

The installer downloads the GitHub source archive for the requested tag,
creates a local virtual environment, and installs the project into that venv.

## Releasing

1. Update the changelog or release notes.
2. Run the local checks.
3. Tag the commit with a semver tag such as `v0.1.0`.
4. Push the tag and create the GitHub release from that tag.

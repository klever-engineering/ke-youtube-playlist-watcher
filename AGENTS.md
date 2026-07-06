# ke-youtube-playlist-watcher

This repository contains a releaseable YouTube playlist watcher that detects
new videos, fetches transcripts, and produces structured analysis reports.

## Working Rules

- Keep the project free of personal-life assumptions and private identifiers.
- Prefer environment variables and example config files over hard-coded values.
- Keep runtime state under `data/` and out of version control.
- Treat tagged releases as the public consumption surface.
- Keep release and install instructions in `README.md`.

## Core Commands

```bash
./scripts/check-playlist
./scripts/check-playlist full
./scripts/install.sh
```


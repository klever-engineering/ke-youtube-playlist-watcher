"""Configuration for the YouTube playlist watcher."""

from __future__ import annotations

import os
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(_env("YTW_DATA_DIR", str(REPO_ROOT / "data")))
STATE_FILE = DATA_DIR / "state.json"
PENDING_DIR = DATA_DIR / "pending"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
ANALYSES_DIR = DATA_DIR / "analyses"

PLAYLIST_ID = _env("YTW_PLAYLIST_ID")
PLAYLIST_TITLE = _env("YTW_PLAYLIST_TITLE", "YouTube playlist")
SCAN_INTERVAL_SECONDS = int(_env("YTW_SCAN_INTERVAL_SECONDS", "1800"))
USER_AGENT = _env("YTW_USER_AGENT", "ke-youtube-playlist-watcher/1.0")
TRANSCRIPT_LANGUAGES = [
    lang.strip()
    for lang in _env("YTW_TRANSCRIPT_LANGUAGES", "en,es,de,fr,it,pt").split(",")
    if lang.strip()
]
MAX_TRANSCRIPT_CHARS = int(_env("YTW_MAX_TRANSCRIPT_CHARS", "32000"))
CONTEXT_FILES = [
    Path(item).expanduser()
    for item in _env("YTW_CONTEXT_FILES").split(os.pathsep)
    if item.strip()
]


def playlist_url() -> str:
    if not PLAYLIST_ID:
        raise ValueError("YTW_PLAYLIST_ID is required")
    return f"https://www.youtube.com/feeds/videos.xml?playlist_id={PLAYLIST_ID}"


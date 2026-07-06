"""Loop memory for the playlist watcher."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

try:
    from . import config
except ImportError:  # pragma: no cover
    import config  # type: ignore[no-redef]

logger = logging.getLogger(__name__)

MEMORY_FILE = config.DATA_DIR / "MEMORY.md"


def generate(
    summary: dict[str, Any],
    scan_kind: str = "quick",
    transcript_fetch_ok: bool | None = None,
) -> str:
    """Generate a compact state note for the latest scan."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    new_videos = summary.get("new_videos", [])
    pending = summary.get("pending_count", 0)
    processed = summary.get("processed_count", 0)

    sections = [
        "# YouTube Playlist Watcher Memory",
        "",
        f"Generated: {now}",
        f"Mode: {scan_kind}",
        f"Playlist: {summary.get('playlist_title', '?')}",
        f"Total videos: {summary.get('total_videos', 0)}",
        f"Processed: {processed}",
        f"Pending: {pending}",
        f"Transcript fetch: {'ok' if transcript_fetch_ok else 'unknown or unavailable'}",
    ]

    if summary.get("error"):
        sections += ["", f"## Error", f"- {summary['error']}"]
    elif new_videos:
        sections += ["", "## New videos"]
        for video in new_videos[:20]:
            sections.append(
                f"- [{video.get('video_id', '?')}] {video.get('title', '?')[:80]}"
            )
    else:
        sections += ["", "## New videos", "- none"]

    sections += [
        "",
        "## State",
        f"- Pending analysis: {pending}",
        f"- Processed count: {processed}",
    ]

    return "\n".join(sections) + "\n"


def write_memory(content: str) -> str:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(content)
    return str(MEMORY_FILE)


def append_run_log(summary: dict[str, Any], scan_kind: str = "quick") -> None:
    now = datetime.now(timezone.utc).isoformat()
    entry = {
        "ts": now,
        "kind": scan_kind,
        "playlist": summary.get("playlist_title"),
        "total": summary.get("total_videos", 0),
        "processed": summary.get("processed_count", 0),
        "new": len(summary.get("new_videos", [])),
        "pending": summary.get("pending_count", 0),
        "error": bool(summary.get("error")),
    }
    log_path = config.DATA_DIR / "run-log.jsonl"
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as handle:
        handle.write(json.dumps(entry) + "\n")


def get_memory_summary() -> dict[str, Any]:
    log_path = config.DATA_DIR / "run-log.jsonl"
    runs: list[dict[str, Any]] = []
    if log_path.exists():
        for line in log_path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                runs.append(json.loads(line))
            except json.JSONDecodeError:
                logger.debug("Skipping corrupt run-log entry")
    total_runs = len(runs)
    recent_errors = sum(1 for run in runs[-10:] if run.get("error"))
    total_new = sum(int(run.get("new", 0)) for run in runs)
    return {
        "total_runs": total_runs,
        "recent_errors_last_10": recent_errors,
        "total_new_videos_found": total_new,
        "last_run": runs[-1]["ts"] if runs else None,
    }


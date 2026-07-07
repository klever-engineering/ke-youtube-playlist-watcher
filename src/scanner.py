"""Playlist scanner: detect new videos, fetch metadata, and queue transcripts."""

from __future__ import annotations

import json
import logging
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

try:
    from . import config
    from . import memory
except ImportError:  # pragma: no cover
    import config  # type: ignore[no-redef]
    import memory  # type: ignore[no-redef]

logger = logging.getLogger(__name__)


def _load_state() -> dict[str, Any]:
    if config.STATE_FILE.exists():
        return json.loads(config.STATE_FILE.read_text())
    return {"processed": {}, "last_scan": None}


def _save_state(state: dict[str, Any]) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")


def _playlist_url() -> str:
    if not config.PLAYLIST_ID:
        raise ValueError("YTW_PLAYLIST_ID is required")
    return f"https://youtube.com/playlist?list={config.PLAYLIST_ID}"


def _fetch_playlist_videos() -> list[dict[str, str]]:
    """Get all videos from the YouTube playlist via yt-dlp."""
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--no-update",
                "--flat-playlist",
                "--dump-json",
                "--playlist-items",
                "1-500",
                _playlist_url(),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            logger.error("yt-dlp playlist fetch failed: %s", result.stderr[:300])
            return []
    except Exception as exc:
        logger.error("yt-dlp playlist error: %s", exc)
        return []

    entries: list[dict[str, str]] = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            logger.warning("yt-dlp JSON parse error in line: %s", line[:100])
            continue
        video_id = entry.get("id", "")
        if not video_id:
            continue
        entries.append(
            {
                "video_id": video_id,
                "title": entry.get("title", ""),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "published": entry.get("upload_date", ""),
                "channel": entry.get("channel", ""),
            }
        )
    return entries


def _fetch_metadata(video_id: str) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--no-update",
                "--print",
                "%(duration)s|%(description)s|%(upload_date)s|%(channel)s|%(view_count)s|%(tags)s",
                f"https://www.youtube.com/watch?v={video_id}",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            logger.warning("yt-dlp metadata failed for %s: %s", video_id, result.stderr[:200])
            return {}
        parts = result.stdout.strip().split("|", 5)
        if len(parts) < 4:
            return {}
        return {
            "duration_seconds": parts[0] if parts[0] != "NA" else "",
            "description": parts[1][:2000] if len(parts) > 1 else "",
            "upload_date": parts[2] if len(parts) > 2 else "",
            "channel": parts[3] if len(parts) > 3 else "",
            "view_count": parts[4] if len(parts) > 4 and parts[4] != "NA" else "",
            "tags": parts[5] if len(parts) > 5 else "",
        }
    except Exception as exc:
        logger.warning("yt-dlp error for %s: %s", video_id, exc)
        return {}


def _fetch_transcript(video_id: str) -> str | None:
    txt_path = config.TRANSCRIPTS_DIR / f"{video_id}.txt"
    if txt_path.exists():
        return txt_path.read_text()

    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # noqa: PLC0415
    except ImportError:
        logger.error("youtube_transcript_api not installed")
        return None

    try:
        api = YouTubeTranscriptApi()
        transcript = None
        for lang in config.TRANSCRIPT_LANGUAGES:
            try:
                transcript = api.fetch(video_id, languages=[lang])
                break
            except Exception:
                continue
        if transcript is None:
            transcript = api.fetch(video_id)

        full_text = " ".join(f"[{segment.start:.1f}s] {segment.text}" for segment in transcript)
        if len(full_text) > config.MAX_TRANSCRIPT_CHARS:
            full_text = full_text[: config.MAX_TRANSCRIPT_CHARS] + "\n\n[... truncated ...]"

        config.TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        txt_path.write_text(full_text)
        return full_text
    except Exception as exc:
        logger.warning("Transcript fetch failed for %s: %s", video_id, exc)
        return None


def _queue_for_analysis(video_data: dict[str, Any]) -> str | None:
    config.PENDING_DIR.mkdir(parents=True, exist_ok=True)
    pending_id = f"yt-{video_data['video_id']}"
    pending_path = config.PENDING_DIR / f"{pending_id}.json"
    if pending_path.exists():
        logger.info("Already pending: %s", pending_id)
        return None
    pending_path.write_text(json.dumps(video_data, indent=2, default=str) + "\n")
    logger.info("Queued: %s", pending_id)
    return pending_id


def scan() -> list[str]:
    state = _load_state()
    entries = _fetch_playlist_videos()
    logger.info("Playlist has %d video(s)", len(entries))

    new_pending: list[str] = []
    for entry in entries:
        video_id = entry["video_id"]
        if video_id in state["processed"]:
            continue

        logger.info("New: [%s] %s", video_id, entry["title"][:80])
        metadata = _fetch_metadata(video_id)
        time.sleep(0.5)
        transcript = _fetch_transcript(video_id)

        video_data = {
            **entry,
            **metadata,
            "transcript": transcript,
            "transcript_available": transcript is not None,
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }

        pending_id = _queue_for_analysis(video_data)
        if pending_id:
            new_pending.append(pending_id)
            state["processed"][video_id] = {
                "title": entry["title"][:200],
                "detected_at": video_data["detected_at"],
                "transcript_available": transcript is not None,
            }

    try:
        summary = check_now()
        transcript_ok = any(
            state["processed"].get(video_id, {}).get("transcript_available")
            for video_id in list(state["processed"].keys())[-5:]
        ) if state["processed"] else None
        mem = memory.generate(summary, scan_kind="full", transcript_fetch_ok=transcript_ok)
        memory.write_memory(mem)
        memory.append_run_log(summary, scan_kind="full")
    except Exception as exc:
        logger.warning("Failed to write loop memory: %s", exc)

    state["last_scan"] = datetime.now(timezone.utc).isoformat()
    _save_state(state)
    return new_pending


def get_pending_videos() -> list[dict[str, Any]]:
    if not config.PENDING_DIR.exists():
        return []
    pending: list[dict[str, Any]] = []
    for path in sorted(config.PENDING_DIR.glob("yt-*.json")):
        try:
            pending.append(json.loads(path.read_text()))
        except json.JSONDecodeError:
            logger.warning("Corrupt pending file: %s", path)
    return pending


def mark_analyzed(video_id: str) -> None:
    pending_path = config.PENDING_DIR / f"yt-{video_id}.json"
    if pending_path.exists():
        config.ANALYSES_DIR.mkdir(parents=True, exist_ok=True)
        pending_path.rename(config.ANALYSES_DIR / f"yt-{video_id}.json")
        logger.info("Marked analyzed: %s", video_id)


def check_now() -> dict[str, Any]:
    state = _load_state()
    try:
        entries = _fetch_playlist_videos()
    except Exception as exc:
        return {
            "error": str(exc),
            "entries": [],
            "new": [],
            "processed": len(state.get("processed", {})),
        }

    new_videos = [entry for entry in entries if entry["video_id"] not in state.get("processed", {})]
    pending_count = len(list(config.PENDING_DIR.glob("yt-*.json"))) if config.PENDING_DIR.exists() else 0
    result = {
        "playlist_title": config.PLAYLIST_TITLE,
        "total_videos": len(entries),
        "new_videos": new_videos,
        "processed_count": len(state.get("processed", {})),
        "pending_count": pending_count,
        "last_scan": state.get("last_scan"),
    }

    try:
        mem = memory.generate(result, scan_kind="quick")
        memory.write_memory(mem)
        memory.append_run_log(result, scan_kind="quick")
    except Exception as exc:
        logger.warning("Failed to write loop memory: %s", exc)

    return result

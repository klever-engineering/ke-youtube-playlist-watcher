"""Prompt rendering helpers for playlist videos."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    from . import analyzer
    from . import config
    from . import scanner
except ImportError:  # pragma: no cover
    import analyzer  # type: ignore[no-redef]
    import config  # type: ignore[no-redef]
    import scanner  # type: ignore[no-redef]


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return value.strip()


def _resolve_context_files(raw: str) -> list[Path]:
    return [Path(item).expanduser() for item in raw.split(os.pathsep) if item.strip()]


def _find_video(video_id: str) -> dict[str, str] | None:
    for entry in scanner._fetch_playlist_videos():  # type: ignore[attr-defined]
        if entry["video_id"] == video_id:
            return entry
    return None


def render_prompt(
    *,
    video_id: str = "",
    playlist_id: str = "",
    playlist_title: str = "",
    context_files: str = "",
) -> tuple[str, dict[str, Any]]:
    if playlist_id:
        config.PLAYLIST_ID = playlist_id
    if playlist_title:
        config.PLAYLIST_TITLE = playlist_title
    if context_files:
        config.CONTEXT_FILES = _resolve_context_files(context_files)

    if video_id:
        video = _find_video(video_id)
        if video is None:
            raise SystemExit(f"Video not found in playlist: {video_id}")
    else:
        entries = scanner._fetch_playlist_videos()
        if not entries:
            raise SystemExit("No videos found in playlist")
        video = entries[0]

    resolved_video_id = video["video_id"]
    metadata = scanner._fetch_metadata(resolved_video_id)  # type: ignore[attr-defined]
    transcript = scanner._fetch_transcript(resolved_video_id)  # type: ignore[attr-defined]
    video_data: dict[str, Any] = {
        **video,
        **metadata,
        "transcript": transcript,
        "transcript_available": transcript is not None,
    }
    return analyzer.build_analysis_prompt(video_data), video_data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render an analysis prompt for a playlist video.")
    parser.add_argument("--video-id", default="", help="Optional explicit YouTube video id.")
    parser.add_argument("--playlist-id", default=_env("YTW_PLAYLIST_ID"))
    parser.add_argument("--playlist-title", default=_env("YTW_PLAYLIST_TITLE", "YouTube playlist"))
    parser.add_argument("--context-files", default=_env("YTW_CONTEXT_FILES"))
    parser.add_argument("--output", default="", help="Optional output file path.")
    args = parser.parse_args(argv)

    prompt, video_data = render_prompt(
        video_id=args.video_id,
        playlist_id=args.playlist_id,
        playlist_title=args.playlist_title,
        context_files=args.context_files,
    )

    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(prompt)
        print(
            json.dumps(
                {"ok": True, "output": str(output_path), "video_id": video_data["video_id"]},
                indent=2,
            )
        )
    else:
        print(prompt)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

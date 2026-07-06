"""Analysis helpers for pending playlist videos."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from . import config
except ImportError:  # pragma: no cover
    import config  # type: ignore[no-redef]


def _list_pending_files() -> list[Path]:
    if not config.PENDING_DIR.exists():
        return []
    return sorted(config.PENDING_DIR.glob("yt-*.json"))


def get_next_pending() -> dict[str, Any] | None:
    pending = _list_pending_files()
    if not pending:
        return None
    return json.loads(pending[0].read_text())


def pending_count() -> int:
    return len(_list_pending_files())


def load_context() -> str:
    sections: list[str] = []
    for path in config.CONTEXT_FILES:
        if not path.exists() or not path.is_file():
            continue
        try:
            sections.append(f"## {path.name}\n{path.read_text()[:3000]}")
        except OSError:
            continue
    return "\n\n---\n\n".join(sections)


def build_analysis_prompt(video_data: dict[str, Any]) -> str:
    context = load_context()
    title = video_data.get("title", "Unknown")
    channel = video_data.get("channel", "Unknown")
    url = video_data.get("url", "")
    description = video_data.get("description", "")[:1500]
    transcript = video_data.get("transcript", "")
    if transcript is None:
        transcript = "[No transcript available - analyze from title/description only]"

    return f"""# YouTube Video Analysis

## Video Info
- **Title:** {title}
- **Channel:** {channel}
- **URL:** {url}
- **Description:** {description}

## Transcript
{transcript[:12000]}

## Optional Context
{context[:5000]}

---

## Analysis Required

Analyze this video and produce a structured report with these sections:

### 1. Executive Summary
2-3 sentences on what this video is about and its core message.

### 2. Key Ideas & Concepts
Extract the main ideas, concepts, mental models, or frameworks presented.
For each one:
- Name the idea
- Explain it in 2-3 sentences
- Note the timestamp if available

### 3. Links & References
List any tools, books, papers, people, or resources mentioned.

### 4. Context Mapping
For each key idea, determine:
- Which configured context file or theme it relates to
- Coverage assessment:
  - ALREADY_COVERED: substantial coverage exists
  - PARTIALLY_COVERED: some coverage exists
  - NOT_COVERED: new territory
  - NOT_APPLICABLE: outside the configured scope

### 5. Follow-up Ideas
For ideas rated PARTIALLY_COVERED or NOT_COVERED, propose concrete next steps.

### 6. Quick Wins
Any immediately applicable insights that require zero or minimal effort.

### 7. Overall Assessment
- **Relevance score:** 1-10
- **Actionability score:** 1-10
- **Recommended priority:** now | soon | someday | reference_only
"""


def save_analysis(video_id: str, analysis_text: str) -> Path:
    config.ANALYSES_DIR.mkdir(parents=True, exist_ok=True)
    analysis_path = config.ANALYSES_DIR / f"yt-{video_id}-analysis.md"
    analysis_path.write_text(analysis_text)

    pending_path = config.PENDING_DIR / f"yt-{video_id}.json"
    if pending_path.exists():
        pending_path.rename(config.ANALYSES_DIR / f"yt-{video_id}.json")

    return analysis_path


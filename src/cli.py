"""Command-line entrypoint for the playlist watcher."""

from __future__ import annotations

import argparse
import json
import sys

try:
    from .memory import get_memory_summary
    from .scanner import check_now, scan
except ImportError:  # pragma: no cover
    from memory import get_memory_summary  # type: ignore[no-redef]
    from scanner import check_now, scan  # type: ignore[no-redef]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        nargs="?",
        choices=("quick", "full"),
        default="quick",
        help="Quick check or full scan.",
    )
    args = parser.parse_args(argv)

    if args.mode == "full":
        result = scan()
        print(json.dumps({"status": "ok", "queued": result}, indent=2, default=str))
    else:
        result = check_now()
        print(json.dumps(result, indent=2, default=str))

    try:
        mem = get_memory_summary()
        if mem["total_runs"] > 0:
            print()
            print("--- Memory ---")
            print("Total runs: " + str(mem["total_runs"]))
            print("Last run:   " + str(mem["last_run"]))
            print("New videos found (all time): " + str(mem["total_new_videos_found"]))
            if mem["recent_errors_last_10"] > 0:
                print("Errors in last 10 runs: " + str(mem["recent_errors_last_10"]))
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


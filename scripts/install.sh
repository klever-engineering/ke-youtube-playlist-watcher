#!/usr/bin/env bash
set -euo pipefail

REPO="${YTW_RELEASE_REPO:-klever-engineering/ke-youtube-playlist-watcher}"
VERSION="${YTW_RELEASE_VERSION:-latest}"
TARGET_DIR="${YTW_INSTALL_DIR:-$HOME/.local/share/ke-youtube-playlist-watcher}"

usage() {
  cat <<'EOF'
Usage: scripts/install.sh [--repo ORG/REPO] [--version TAG|latest] [--target-dir PATH]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO="${2:?missing repo}"
      shift 2
      ;;
    --version)
      VERSION="${2:?missing version}"
      shift 2
      ;;
    --target-dir)
      TARGET_DIR="${2:?missing target dir}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

python3 - "$REPO" "$VERSION" "$TARGET_DIR" <<'PY'
import json
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

repo, version, target_dir = sys.argv[1:4]

def latest_release(repo_name: str) -> str:
    url = f"https://api.github.com/repos/{repo_name}/releases/latest"
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    tag = payload.get("tag_name")
    if not tag:
        raise SystemExit(f"Could not determine latest release for {repo_name}")
    return tag

if version == "latest":
    version = latest_release(repo)

archive_url = f"https://api.github.com/repos/{repo}/tarball/{version}"
target = pathlib.Path(target_dir).expanduser().resolve()
target.mkdir(parents=True, exist_ok=True)

def _safe_extract(tar: tarfile.TarFile, destination: pathlib.Path) -> None:
    destination = destination.resolve()
    for member in tar.getmembers():
        member_path = (destination / member.name).resolve()
        if destination not in member_path.parents and member_path != destination:
            raise SystemExit(f"Blocked unsafe tar entry: {member.name}")
    tar.extractall(destination)

with tempfile.TemporaryDirectory() as tmpdir:
    archive_path = pathlib.Path(tmpdir) / "source.tar.gz"
    request = urllib.request.Request(archive_url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=60) as response, archive_path.open("wb") as handle:
        shutil.copyfileobj(response, handle)

    extract_dir = pathlib.Path(tmpdir) / "src"
    extract_dir.mkdir()
    with tarfile.open(archive_path, "r:gz") as tar:
        _safe_extract(tar, extract_dir)

    repo_root = next(path for path in extract_dir.iterdir() if path.is_dir())
    venv_dir = target / ".venv"
    if not venv_dir.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    pip = venv_dir / "bin" / "pip"
    subprocess.run([str(pip), "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(pip), "install", str(repo_root)], check=True)

    (target / "VERSION").write_text(f"{version}\n")
    print(f"Installed {repo}@{version} into {target}")
PY

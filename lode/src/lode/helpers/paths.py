"""Shared repo-root resolution, usable by any tool. Same pattern as the
per-tool copies (e.g. checklist/_paths.py) predating this — this is the
consolidated home for new tools; existing tools haven't been migrated yet."""

from pathlib import Path


def find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".git").exists():
            return parent
    raise FileNotFoundError(f"No .git directory found above {start}")

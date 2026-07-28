"""Shared repo-root resolution for the checklist tools — same pattern as
lode/src/lode/tools/statcan/_datasets.py's resolve_output, so scripts here
work regardless of the invoking cwd or where the data actually lives."""

from pathlib import Path


def find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".git").exists():
            return parent
    raise FileNotFoundError(f"No .git directory found above {start}")

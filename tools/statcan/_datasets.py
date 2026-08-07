"""Shared dataset-config lookup for the statcan fetch scripts."""

from pathlib import Path

import yaml

DEFAULT_CONFIG = Path(__file__).parent / "datasets.yaml"


def load_dataset(dataset: str, config_path: Path) -> dict:
    with open(config_path) as f:
        datasets = yaml.safe_load(f)
    if dataset not in datasets:
        available = ", ".join(datasets)
        raise KeyError(f"Unknown dataset '{dataset}'. Available: {available}")
    return datasets[dataset]


def find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".git").exists():
            return parent
    raise FileNotFoundError(f"No .git directory found above {start}")


def resolve_output(output: str, script_file: str) -> Path:
    """Resolve an output path from datasets.yaml relative to the repo root,
    not the caller's cwd — so the script writes to the same place regardless
    of what directory it's invoked from."""
    path = Path(output)
    if path.is_absolute():
        return path
    return find_repo_root(Path(script_file).resolve()) / path

#!/usr/bin/env python3
"""Runs pipeline stages/steps from lode.config.yaml, per source. Steps are
dotted import paths, resolved and run in order; output persists only at
stage boundaries.

Usage:
    python run.py                                # everything, all sources
    python run.py --stage preprocessing          # one stage, all sources
    python run.py --source on_toronto_cycling    # one source, all stages
"""

import argparse
import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

HELPERS_DIR = Path(__file__).resolve().parent.parent / "helpers"
sys.path.insert(0, str(HELPERS_DIR))
from config import load_config  # noqa: E402
from readers import read_source_file  # noqa: E402

# So step references like "lode.pipeline.steps.column_map:apply" resolve as
# real (implicit namespace) package imports, not another sys.path hack.
LODE_SRC = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(LODE_SRC))

CONFIG = load_config(Path(__file__).resolve())
REPO_ROOT = CONFIG["repo_root"]
SOURCES_DIR = REPO_ROOT / CONFIG["sources_dir"]
RAW_DIR = REPO_ROOT / CONFIG["raw_dir"]
STAGES = CONFIG["pipeline"]["stages"]


def list_source_ids() -> list:
    if not SOURCES_DIR.is_dir():
        return []
    return sorted(p.name for p in SOURCES_DIR.iterdir() if p.is_dir())


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {} if path.exists() else {}


def resolve_step(ref: str):
    """'module.path:function_name' -> the actual function."""
    module_path, _, func_name = ref.partition(":")
    module = importlib.import_module(module_path)
    return getattr(module, func_name)


def load_stage_input(stage_index: int, source_id: str):
    if stage_index == 0:
        metadata = load_yaml(SOURCES_DIR / source_id / "metadata.yaml")
        raw_filename = metadata.get("raw_filename")
        fmt = metadata.get("format")
        if not raw_filename or not fmt:
            raise ValueError("metadata.yaml is missing raw_filename and/or format")
        raw_path = RAW_DIR / source_id / raw_filename
        if not raw_path.exists():
            raise FileNotFoundError(f"raw file not found: {raw_path}")
        return read_source_file(raw_path, fmt)

    prev_output_dir = REPO_ROOT / STAGES[stage_index - 1]["output_dir"]
    input_path = prev_output_dir / source_id / f"{source_id}.parquet"
    if not input_path.exists():
        raise FileNotFoundError(f"expected {input_path} — did the previous stage run for this source?")
    return read_source_file(input_path, "parquet")


def format_entry(entry: dict) -> str:
    header = f"{entry['timestamp']} [{entry['stage']}] {entry['source_id']}: {entry['status']}"
    if entry["status"] == "error":
        return f"{header} — {entry['error']}"
    lines = [f"{header} ({entry['rows_before']} -> {entry['rows_after']} rows)"]
    for step_log in entry["steps"]:
        for warning in step_log.get("warnings", []):
            lines.append(f"    {step_log['step']}: {warning}")
    return "\n".join(lines)


def run_stage(stage: dict, stage_index: int, source_ids: list) -> list:
    output_dir = REPO_ROOT / stage["output_dir"]
    steps = [(ref, resolve_step(ref)) for ref in stage.get("steps", [])]

    log_entries = []
    for source_id in source_ids:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": stage["name"],
            "source_id": source_id,
        }
        try:
            data = load_stage_input(stage_index, source_id)
            rows_before = len(data)

            step_logs = []
            for ref, step in steps:
                data, step_log = step(data, source_id=source_id, config=CONFIG)
                step_logs.append({"step": ref, **(step_log or {})})

            out_path = output_dir / source_id / f"{source_id}.parquet"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            data.to_parquet(out_path)

            entry.update({
                "status": "ok",
                "rows_before": rows_before,
                "rows_after": len(data),
                "steps": step_logs,
            })
        except Exception as e:
            entry.update({"status": "error", "error": str(e)})

        log_entries.append(entry)
        print(format_entry(entry))

    return log_entries


def write_logs(log_entries: list) -> Path:
    log_dir = REPO_ROOT / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    jsonl_path = log_dir / f"pipeline_{stamp}.jsonl"
    with open(jsonl_path, "w") as f:
        for entry in log_entries:
            f.write(json.dumps(entry, default=str) + "\n")

    log_path = log_dir / f"pipeline_{stamp}.log"
    with open(log_path, "w") as f:
        f.write("\n".join(format_entry(entry) for entry in log_entries) + "\n")

    return log_path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", help="Only run this stage (by name)")
    parser.add_argument("--source", help="Only run this source (by source_id)")
    args = parser.parse_args()

    stage_names = [s["name"] for s in STAGES]
    if args.stage and args.stage not in stage_names:
        sys.exit(f"No such stage: {args.stage} (known: {', '.join(stage_names)})")
    stages_to_run = [s for s in STAGES if not args.stage or s["name"] == args.stage]
    source_ids = [args.source] if args.source else list_source_ids()

    all_log_entries = []
    for stage in stages_to_run:
        stage_index = stage_names.index(stage["name"])
        all_log_entries.extend(run_stage(stage, stage_index, source_ids))

    log_path = write_logs(all_log_entries)
    ok = sum(1 for e in all_log_entries if e["status"] == "ok")
    print(f"\n{ok}/{len(all_log_entries)} succeeded. Log: {log_path}")


if __name__ == "__main__":
    main()

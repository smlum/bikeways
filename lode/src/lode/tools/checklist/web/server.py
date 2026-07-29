#!/usr/bin/env python3
"""Local web UI for working through checklist.csv in a browser instead of
editing the raw CSV. This stage only fills in the checklist itself (found/
not-found, source_url, notes) — it does not scaffold source yaml files.
Run process_checklist.py separately, whenever you're ready, to turn
confirmed source_url rows into sources/datasets/<id>.yaml files.

Usage:
    python server.py
Then open http://localhost:8642
"""

import sys
from datetime import date
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

CHECKLIST_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CHECKLIST_DIR))
from _paths import find_repo_root  # noqa: E402

REPO_ROOT = find_repo_root(Path(__file__).resolve())
CHECKLIST_CSV = REPO_ROOT / "sources" / "checklist.csv"

app = Flask(__name__, static_folder=str(Path(__file__).parent), static_url_path="")


def load_checklist() -> pd.DataFrame:
    return pd.read_csv(CHECKLIST_CSV, dtype=str).fillna("")


def save_checklist(df: pd.DataFrame):
    df.to_csv(CHECKLIST_CSV, index=False)


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/meta")
def api_meta():
    return jsonify({"checklist_path": str(CHECKLIST_CSV.relative_to(REPO_ROOT))})


@app.route("/api/rows")
def api_rows():
    df = load_checklist().reset_index().rename(columns={"index": "row_index"})
    return jsonify(df.to_dict(orient="records"))


@app.route("/api/found", methods=["POST"])
def api_found():
    data = request.get_json()
    row_index = int(data["row_index"])
    source_url = (data.get("source_url") or "").strip()
    if not source_url:
        return jsonify({"error": "source_url required"}), 400

    df = load_checklist()
    if row_index not in df.index:
        return jsonify({"error": "row not found"}), 404

    today = str(date.today())
    df.at[row_index, "source_url"] = source_url
    df.at[row_index, "checked"] = "x"
    df.at[row_index, "checked_date"] = today
    save_checklist(df)
    return jsonify({"checked_date": today})


@app.route("/api/not_found", methods=["POST"])
def api_not_found():
    data = request.get_json()
    row_index = int(data["row_index"])
    notes = (data.get("notes") or "").strip()

    df = load_checklist()
    if row_index not in df.index:
        return jsonify({"error": "row not found"}), 404

    today = str(date.today())
    df.at[row_index, "checked"] = "x"
    df.at[row_index, "checked_date"] = today
    # Retract any previously recorded source_url/source_ids (e.g. correcting a
    # mistaken "Found"). prior_url (the permanent CCND-lead reference, if any)
    # is never touched here, so it's never lost to a retraction.
    df.at[row_index, "source_url"] = ""
    df.at[row_index, "source_ids"] = ""
    if notes:
        existing = df.at[row_index, "notes"]
        df.at[row_index, "notes"] = f"{existing}; {notes}" if existing else notes
    save_checklist(df)
    return jsonify({"checked_date": today})


@app.route("/api/note", methods=["POST"])
def api_note():
    data = request.get_json()
    row_index = int(data["row_index"])
    notes = data.get("notes") or ""

    df = load_checklist()
    if row_index not in df.index:
        return jsonify({"error": "row not found"}), 404

    df.at[row_index, "notes"] = notes
    save_checklist(df)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, port=8642)

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from study_context import DEFAULT_RQ_SUMMARY, DEFAULT_CODES, PRELIMINARY_THEMES, GROUP_INFO

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "project_data"
STATE_PATH = DATA_DIR / "project_state.json"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
BACKUP_DIR = DATA_DIR / "backups"
EXPORT_DIR = PROJECT_ROOT / "exports"


def ensure_folders() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    TRANSCRIPTS_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)
    EXPORT_DIR.mkdir(exist_ok=True)


def default_state() -> Dict[str, Any]:
    ensure_folders()
    return {
        "project_name": "SPARK Nudging Interview Analysis",
        "analysis_version": "v1.0-provisional",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "transcripts": [],
        "uploads": [],
        "codebook": DEFAULT_CODES,
        "themes": PRELIMINARY_THEMES,
        "rq_summary": DEFAULT_RQ_SUMMARY,
        "coding": [],
        "participant_summaries": [],
        "audit_log": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "Initial project scaffold created",
                "type": "system",
            }
        ],
        "analysis_status": "Provisional analysis loaded",
        "analysis_markers": {
            "ai_suggestions": "Available only as suggestions; researcher review required",
            "manual_review_required": True,
            "automated_analysis": "Unavailable",
        },
        "study_context": {
            "condition_map": GROUP_INFO,
            "rq_reference": "See workbook mapping and interview protocol",
        },
    }


def load_state() -> Dict[str, Any]:
    ensure_folders()
    if not STATE_PATH.exists():
        state = default_state()
        save_state(state)
        return state
    with STATE_PATH.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    for key in ["codebook", "themes", "rq_summary", "coding", "transcripts", "uploads", "participant_summaries", "audit_log"]:
        if key not in data:
            data[key] = default_state()[key]
    return data


def save_state(state: Dict[str, Any]) -> None:
    ensure_folders()
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    with STATE_PATH.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)


def append_audit(state: Dict[str, Any], event: str, event_type: str = "system", details: Dict[str, Any] | None = None) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "type": event_type,
    }
    if details:
        entry["details"] = details
    state.setdefault("audit_log", []).append(entry)
    save_state(state)


def write_project_backup(state: Dict[str, Any]) -> Path:
    ensure_folders()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"project_backup_{ts}.json"
    with backup_path.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
    return backup_path

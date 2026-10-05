from __future__ import annotations

import hashlib
import io
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

from docx import Document

from study_context import GROUP_INFO


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_text(raw: str) -> str:
    if raw is None:
        return ""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.splitlines())


def detect_group_from_filename(filename: str) -> Tuple[str | None, str | None, List[str]]:
    warnings: List[str] = []
    name = Path(filename).stem
    match = re.search(r"(?i)(1A|1B|2A|2B)", name)
    group = match.group(1).upper() if match else None
    participant = None
    participant_match = re.search(r"(?i)(?:P|Participant|participant)[-_ ]?(\d+)", name)
    if participant_match:
        participant = "P" + participant_match.group(1)
    elif re.search(r"(?i)(study[12][AB]|participant[s]?[-_ ]?[A-Z]?[0-9]+)", name):
        warnings.append("Participant ID may be ambiguous; confirm before analysis.")
    if group and group not in GROUP_INFO:
        warnings.append(f"Unknown study group {group}; expected 1A, 1B, 2A, 2B.")
    return participant, group, warnings


def parse_docx_text(file_bytes: bytes) -> str:
    document = Document(io.BytesIO(file_bytes))
    paras = []
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            paras.append(text)
    return "\n\n".join(paras)


def parse_txt_text(file_bytes: bytes) -> str:
    return normalize_text(file_bytes.decode("utf-8", errors="replace"))


def parse_transcript_bytes(filename: str, file_bytes: bytes) -> Dict[str, Any]:
    lower = filename.lower()
    if lower.endswith(".docx"):
        text = parse_docx_text(file_bytes)
    elif lower.endswith(".txt"):
        text = parse_txt_text(file_bytes)
    else:
        raise ValueError(f"Unsupported transcript type: {filename}")
    participant_id, group, warnings = detect_group_from_filename(filename)
    if group:
        course_order = GROUP_INFO[group]["course_order"]
        condition = GROUP_INFO[group]["condition"]
    else:
        course_order = "Unconfirmed"
        condition = "Unconfirmed"
    data = {
        "transcript_id": f"transcript_{hashlib.sha1(filename.encode('utf-8')).hexdigest()[:12]}",
        "filename": filename,
        "participant_id": participant_id or "Unassigned",
        "assigned_group": group or "Unassigned",
        "condition": condition,
        "course_order": course_order,
        "word_count": len(text.split()),
        "timestamp_available": bool(re.search(r"\d{1,2}:\d{2}(?::\d{2})?", text[:2000])),
        "status": "Uploaded",
        "source_text": text,
        "content_hash": sha256_bytes(file_bytes),
        "extraction_warnings": warnings,
        "review_status": "Pending",
    }
    return data


def parse_uploaded_files(uploaded_files: List[Any]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for uploaded in uploaded_files:
        name = getattr(uploaded, "name", "")
        file_bytes = uploaded.read() if hasattr(uploaded, "read") else uploaded.getvalue()
        lower = name.lower()
        if lower.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    fname = info.filename
                    if fname.lower().endswith((".txt", ".docx")):
                        records.append(parse_transcript_bytes(fname.split('/')[-1], zf.read(info)))
        elif lower.endswith((".txt", ".docx")):
            records.append(parse_transcript_bytes(name, file_bytes))
        else:
            raise ValueError(f"Unsupported file type: {name}")
    return records

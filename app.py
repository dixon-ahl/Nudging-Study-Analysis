from __future__ import annotations

import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st
from openpyxl import load_workbook

from exports import export_coding_csv, export_json_backup, export_rq_report, export_workbook
from storage import EXPORT_DIR, STATE_PATH, ensure_folders, load_state, save_state, write_project_backup
from study_context import DEFAULT_RQ_SUMMARY, GROUP_INFO, PRELIMINARY_THEMES, REVIEW_STATUSES, EVIDENCE_TYPES
from transcripts import parse_uploaded_files

st.set_page_config(page_title="SPARK Nudging Interview Analysis", layout="wide")

DEFAULT_WORKBOOK_CANDIDATES = [
    Path(r"C:\Users\dixon\Downloads\Analysis Workbook.xlsx"),
    Path(r"C:\Users\dixon\Downloads\SPARK_Nudging_Study_Analysis.xlsx"),
    Path(__file__).resolve().parent / "data" / "Analysis Workbook.xlsx",
]


def _normalize_rq_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for row in rows:
        if not row:
            continue
        q = row.get("Research Question") or row.get("RQ") or row.get("Question") or ""
        if "Research Question" in row and row.get("Research Question") is None:
            continue
        if "RQ Code" not in row and q:
            match = re.search(r"RQ\d+[a-zA-Z0-9-]*", str(q))
            row["RQ Code"] = match.group(0) if match else "Unspecified"
        if "Research Question" not in row and q:
            row["Research Question"] = q
        if "Lens" not in row and row.get("RQ Type"):
            row["Lens"] = row.get("RQ Type")
        row["Main Themes"] = [] if row.get("Main Themes") is None else [
            v.strip() for v in str(row.get("Main Themes")).split("\n") if v and v.strip()
        ]
        row["Participant IDs"] = [] if row.get("Participant IDs") is None else [
            v.strip() for v in str(row.get("Participant IDs")).split(",") if v and v.strip()
        ]
        normalized.append(row)
    return normalized


def _normalize_code_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for row in rows:
        if not row:
            continue
        if row.get("Code") is None and row.get("Code ID") is None:
            continue
        normalized.append({
            "code_id": row.get("Code ID") or row.get("code_id") or "",
            "name": row.get("Code") or row.get("name") or "",
            "related_theme": row.get("Related Preliminary Theme") or row.get("related_theme") or "",
            "category": row.get("Category") or row.get("category") or "",
            "include": row.get("Include") or row.get("include") or "",
            "exclude": row.get("Exclude / Interpretive Boundary") or row.get("exclude") or "",
            "excerpt_records": row.get("Excerpt Records") or row.get("excerpt_records") or "",
            "example_excerpt_id": row.get("Example Excerpt ID") or row.get("example_excerpt_id") or "",
        })
    return normalized


def _load_workbook_context(state: Dict[str, Any]) -> Dict[str, Any]:
    for candidate in DEFAULT_WORKBOOK_CANDIDATES:
        if candidate.exists():
            wb = load_workbook(candidate, data_only=True)
            if "RQ Summary" in wb.sheetnames:
                sheet = wb["RQ Summary"]
                rows = list(sheet.iter_rows(values_only=True))
                headers = rows[0] if rows else []
                rq_rows = []
                for r in rows[1:]:
                    row = dict(zip(headers, r))
                    if row.get("Research Question") is None and row.get("RQ") is None:
                        continue
                    rq_rows.append(row)
                if rq_rows:
                    state["rq_summary"] = _normalize_rq_rows(rq_rows)
            if "Codebook" in wb.sheetnames:
                sheet = wb["Codebook"]
                rows = list(sheet.iter_rows(values_only=True))
                headers = rows[0] if rows else []
                codebook = []
                for r in rows[1:]:
                    row = dict(zip(headers, r))
                    if row.get("Code") is None and row.get("Code ID") is None:
                        continue
                    codebook.append(row)
                normalized = _normalize_code_rows(codebook)
                if normalized:
                    state["codebook"] = normalized
            if "Method and Review" in wb.sheetnames:
                sheet = wb["Method and Review"]
                rows = list(sheet.iter_rows(values_only=True))
                if rows and len(rows) > 1:
                    state["analysis_status"] = "Workbook imported and loaded as provisional evidence"
            break
    return state


def _ensure_project_ready() -> Dict[str, Any]:
    state = load_state()
    if not state.get("rq_summary"):
        state["rq_summary"] = [*DEFAULT_RQ_SUMMARY]
    if not state.get("codebook"):
        state["codebook"] = []
    if not state.get("themes"):
        state["themes"] = [*PRELIMINARY_THEMES]
    state = _load_workbook_context(state)
    save_state(state)
    return state


state = _ensure_project_ready()


def _file_to_bytes(file) -> bytes:
    if hasattr(file, "read"):
        return file.read()
    return file.getvalue()


def _participant_df() -> pd.DataFrame:
    rows = []
    for transcript in state.get("transcripts", []):
        rows.append({
            "transcript_id": transcript.get("transcript_id"),
            "participant_id": transcript.get("participant_id"),
            "assigned_group": transcript.get("assigned_group"),
            "condition": transcript.get("condition"),
            "course_order": transcript.get("course_order"),
            "word_count": transcript.get("word_count", 0),
            "status": transcript.get("status", "Uploaded"),
            "review_status": transcript.get("review_status", "Pending"),
            "warnings": "; ".join(transcript.get("extraction_warnings", [])),
            "duplicate": transcript.get("duplicate", False),
        })
    return pd.DataFrame(rows)


def _summary_table() -> pd.DataFrame:
    rows = []
    for key, info in GROUP_INFO.items():
        rows.append({
            "Group": key,
            "Condition": info["condition"],
            "Course order": info["course_order"],
        })
    return pd.DataFrame(rows)


def _participant_coverage() -> pd.DataFrame:
    records = []
    for transcript in state.get("transcripts", []):
        excerpts = [c for c in state.get("coding", []) if c.get("transcript_id") == transcript.get("transcript_id")]
        scopes = sorted({c.get("related_rqs", "") for c in excerpts})
        records.append({
            "participant_id": transcript.get("participant_id"),
            "assigned_group": transcript.get("assigned_group"),
            "condition": transcript.get("condition"),
            "transcript_status": transcript.get("status", "Uploaded"),
            "topic_coverage": ", ".join(scopes) if scopes else "No excerpt-coded evidence yet",
            "excerpt_count": len(excerpts),
            "issue": "; ".join(transcript.get("extraction_warnings", [])) if transcript.get("extraction_warnings") else "None",
        })
    return pd.DataFrame(records)


def _codebook_df() -> pd.DataFrame:
    return pd.DataFrame(state.get("codebook", []))


# ------------------------------
# UI pages
# ------------------------------

with st.sidebar:
    st.title("Navigation")
    page = st.radio(
        "Select a view",
        [
            "Overview",
            "Participants and Uploads",
            "Transcript Coding",
            "Codebook",
            "Themes and Research Questions",
            "Condition Comparison",
            "Review and Export",
        ],
    )
    st.caption(f"Project data: {STATE_PATH.parent}")
    st.caption(f"Analysis status: {state.get('analysis_status', 'Provisional')}")

if page == "Overview":
    st.title("SPARK Nudging Interview Analysis")
    st.caption("Framework Method dashboard for provisional qualitative coding and comparison of reminder conditions.")
    st.markdown("**Important**: AI-generated suggestions are provisional and require researcher approval; they do not replace interpretation.")

    transcript_count = len(state.get("transcripts", []))
    participant_count = len({t.get("participant_id") for t in state.get("transcripts", []) if t.get("participant_id") and t.get("participant_id") != "Unassigned"})
    pending_suggestions = sum(1 for c in state.get("coding", []) if c.get("human_review") in ("Pending", None))
    approved = sum(1 for c in state.get("coding", []) if c.get("human_review") == "Approved")
    themes_count = len(state.get("themes", []))

    cols = st.columns(5)
    cols[0].metric("Participants", participant_count)
    cols[1].metric("Transcripts", transcript_count)
    cols[2].metric("Pending review", pending_suggestions)
    cols[3].metric("Approved excerpts", approved)
    cols[4].metric("Preliminary themes", themes_count)

    st.subheader("Assigned reminder conditions")
    study_table = _summary_table()
    st.dataframe(study_table, use_container_width=True, hide_index=True)

    st.subheader("Participant coverage")
    coverage = _participant_coverage()
    st.dataframe(coverage, use_container_width=True, hide_index=True)

    st.subheader("Research question overview")
    rq_df = pd.DataFrame(state.get("rq_summary", []))
    st.dataframe(rq_df[["RQ Code", "Lens", "Research Question"]], use_container_width=True, hide_index=True)

elif page == "Participants and Uploads":
    st.title("Participants and Uploads")
    st.caption("Upload individual transcripts, ZIP archives or a pre-existing analysis workbook. Ambiguous filenames are flagged rather than guessed.")

    uploaded = st.file_uploader(
        "Upload transcript files or a workbook",
        type=["txt", "docx", "zip", "xlsx"],
        accept_multiple_files=True,
    )

    if uploaded:
        try:
            transcript_records = parse_uploaded_files(list(uploaded))
            for rec in transcript_records:
                rec["duplicate"] = any(
                    existing.get("content_hash") == rec.get("content_hash")
                    for existing in state.get("transcripts", [])
                )
                if not any(existing.get("transcript_id") == rec.get("transcript_id") for existing in state.get("transcripts", [])):
                    state.setdefault("transcripts", []).append(rec)
            state["analysis_status"] = "New transcript uploads processed; provisional review still required"
            save_state(state)
            st.success(f"Loaded {len(transcript_records)} transcript record(s).")
        except Exception as exc:
            st.error(f"Upload failed: {exc}")

        preview = _participant_df()
        if not preview.empty:
            st.subheader("Import preview")
            st.dataframe(preview, use_container_width=True, hide_index=True)

    st.subheader("Import workbook")
    workbook_upload = st.file_uploader("Optional: import an existing workbook for the current project", type=["xlsx"], key="workbook_upload")
    if workbook_upload is not None:
        try:
            wb = load_workbook(workbook_upload, data_only=True)
            if "RQ Summary" in wb.sheetnames:
                rows = list(wb["RQ Summary"].iter_rows(values_only=True))
                headers = rows[0]
                rq_rows = []
                for row in rows[1:]:
                    if row[0] is None:
                        continue
                    pr = dict(zip(headers, row))
                    rq_rows.append(pr)
                state["rq_summary"] = rq_rows
            if "Codebook" in wb.sheetnames:
                rows = list(wb["Codebook"].iter_rows(values_only=True))
                headers = rows[0]
                codebook = []
                for row in rows[1:]:
                    if row[0] is None:
                        continue
                    codebook.append(dict(zip(headers, row)))
                state["codebook"] = codebook
            if "Master Coding" in wb.sheetnames:
                rows = list(wb["Master Coding"].iter_rows(values_only=True))
                if rows:
                    headers = rows[0]
                    coding = []
                    for row in rows[1:]:
                        if row[0] is None:
                            continue
                        coding.append(dict(zip(headers, row)))
                    state["coding"] = coding
            state["analysis_status"] = "Workbook imported into the project"
            save_state(state)
            st.success("Workbook imported successfully.")
        except Exception as exc:
            st.error(f"Workbook import failed: {exc}")

    if state.get("transcripts"):
        st.subheader("Current transcripts in project")
        st.dataframe(_participant_df(), use_container_width=True, hide_index=True)

elif page == "Transcript Coding":
    st.title("Transcript Coding")
    transcripts = state.get("transcripts", [])
    if not transcripts:
        st.info("Upload transcripts to begin coding and review evidence.")
        st.stop()

    transcript_ids = [t.get("transcript_id") for t in transcripts]
    selected_id = st.selectbox("Select participant transcript", transcript_ids, index=0)
    transcript = next((t for t in transcripts if t.get("transcript_id") == selected_id), transcripts[0])

    left, center, right = st.columns([1.4, 2.5, 2.4])

    with left:
        st.subheader("Participants")
        for item in transcripts:
            if item.get("transcript_id") == selected_id:
                selected_style = "border: 2px solid #1f4e79; border-radius: 8px; padding: 0.5rem;"
            else:
                selected_style = "border: 1px solid #dfe6ee; border-radius: 8px; padding: 0.5rem;"
            st.markdown(
                f"<div style='{selected_style}'>"
                f"<strong>{item.get('participant_id', 'Unassigned')}</strong><br>"
                f"Group: {item.get('assigned_group', 'Unassigned')}<br>"
                f"Condition: {item.get('condition', 'Unconfirmed')}<br>"
                f"Words: {item.get('word_count', 0)}"
                f"</div>",
                unsafe_allow_html=True,
            )
            if item.get("transcript_id") != selected_id:
                if st.button("Open", key=f"open_{item.get('transcript_id')}"):
                    selected_id = item.get("transcript_id")
                    st.rerun()

    with center:
        st.subheader(f"Transcript view: {transcript.get('participant_id', 'Unassigned')}")
        text = transcript.get("source_text", "")
        st.caption(f"Assigned group: {transcript.get('assigned_group', 'Unassigned')} | Condition: {transcript.get('condition', 'Unconfirmed')} | Course order: {transcript.get('course_order', 'Unconfirmed')}")
        st.text_area("Transcript text", text, height=480)

        excerpts = [c for c in state.get("coding", []) if c.get("transcript_id") == selected_id]
        if excerpts:
            st.subheader("Existing excerpts")
            for ex in excerpts:
                _id = ex.get("excerpt_id", "exp")
                st.markdown(f"**{_id}** — {ex.get('review_status', 'Pending')} | {ex.get('code_id', '')} | {ex.get('related_rqs', '')}")
                st.write(ex.get("exact_quote", ""))
                if st.button("Focus on this excerpt", key=f"focus_{_id}"):
                    st.session_state["selected_excerpt_id"] = _id
                    st.rerun()

    with right:
        st.subheader("Evidence and review")
        form = st.form("excerpt_form")
        excerpt_text = form.text_area("Enter or paste exact excerpt", value="", height=120)
        code_options = [code.get("name") for code in state.get("codebook", [])]
        selected_codes = form.multiselect("Assign codes", code_options)
        selected_rqs = form.multiselect("Related RQs", ["RQ2a-1", "RQ2a-2", "RQ2a-3", "RQ2a-4"])
        theme_value = form.selectbox("Review status", REVIEW_STATUSES)
        evidence_type = form.selectbox("Evidence type", EVIDENCE_TYPES)
        note_text = form.text_area("Analytic note", value="", height=140)
        submitted = form.form_submit_button("Save excerpt")

        if submitted and excerpt_text.strip():
            code_id = "; ".join([code.get("code_id") for code in state.get("codebook", []) if code.get("name") in selected_codes])
            excerpt_id = f"E{len(state.get('coding', [])) + 1:03d}"
            rec = {
                "transcript_id": selected_id,
                "participant_id": transcript.get("participant_id", "Unassigned"),
                "condition_code": transcript.get("condition", "Unconfirmed"),
                "code_id": code_id,
                "related_rqs": "; ".join(selected_rqs),
                "exact_quote": excerpt_text,
                "timestamp": "",
                "theme": "",
                "subtheme": "",
                "broader_insight_category": "",
                "topic": "",
                "note": note_text,
                "source_file": transcript.get("filename", ""),
                "source_paragraphs": "Manual entry",
                "evidence_type": evidence_type,
                "human_review": theme_value,
                "rq2a_1_included": int("RQ2a-1" in selected_rqs),
                "rq2a_2_included": int("RQ2a-2" in selected_rqs),
                "rq2a_3_included": int("RQ2a-3" in selected_rqs),
                "rq2a_4_included": int("RQ2a-4" in selected_rqs),
                "excerpt_id": excerpt_id,
                "review_status": theme_value,
                "related_rqs": "; ".join(selected_rqs),
            }
            state.setdefault("coding", []).append(rec)
            save_state(state)
            st.success(f"Saved excerpt {excerpt_id} for {transcript.get('participant_id')}.")

        if "selected_excerpt_id" in st.session_state:
            focused = next((c for c in state.get("coding", []) if c.get("excerpt_id") == st.session_state["selected_excerpt_id"]), None)
            if focused:
                st.subheader("Focused excerpt context")
                st.write(focused.get("exact_quote", ""))
                st.caption(f"Excerpt {focused.get('excerpt_id')} | Review: {focused.get('review_status', 'Pending')}")

elif page == "Codebook":
    st.title("Codebook")
    code_df = _codebook_df()
    if code_df.empty:
        st.info("No codebook entries yet. Import a workbook or add a code manually.")
    else:
        st.dataframe(code_df, use_container_width=True, hide_index=True)

    st.subheader("Add a new code")
    with st.form("new_code_form"):
        code_name = st.text_input("Code name")
        category = st.text_input("Category")
        definition = st.text_area("Definition")
        include = st.text_area("Inclusion criteria")
        exclude = st.text_area("Exclusion criteria")
        submitted = st.form_submit_button("Save code")
        if submitted and code_name:
            codebook = state.setdefault("codebook", [])
            codebook.append({
                "code_id": f"C{len(codebook) + 1:02d}",
                "name": code_name,
                "category": category,
                "definition": definition,
                "include": include,
                "exclude": exclude,
                "related_theme": "",
                "rq_codes": [],
            })
            save_state(state)
            st.success("Code added to the codebook.")

elif page == "Themes and Research Questions":
    st.title("Themes and Research Questions")
    st.caption("The workbook's preliminary themes are imported as provisional findings; they are not immutable and may be revised after further coding.")
    rq_df = pd.DataFrame(state.get("rq_summary", []))
    if "RQ Code" not in rq_df.columns and "Research Question" in rq_df.columns:
        rq_df["RQ Code"] = [
            re.search(r"RQ\d+[a-zA-Z0-9-]*", str(q)).group(0) if re.search(r"RQ\d+[a-zA-Z0-9-]*", str(q)) else "Unspecified"
            for q in rq_df["Research Question"].fillna("")
        ]
    st.subheader("RQ summary")
    if not rq_df.empty:
        cols = [c for c in ["RQ Code", "Lens", "Research Question"] if c in rq_df.columns]
        st.dataframe(rq_df[cols], use_container_width=True, hide_index=True)
    st.subheader("Preliminary themes")
    st.dataframe(pd.DataFrame(state.get("themes", [])), use_container_width=True, hide_index=True)

elif page == "Condition Comparison":
    st.title("Condition Comparison")
    transcripts = state.get("transcripts", [])
    if not transcripts:
        st.info("Upload or import participant transcripts to compare reminder conditions.")
        st.stop()
    df = pd.DataFrame(transcripts)
    grouped = df.groupby("condition").agg(participants=("participant_id", "nunique"), transcripts=("transcript_id", "count"))
    st.dataframe(grouped, use_container_width=True)
    st.bar_chart(grouped[["transcripts"]])

    st.subheader("Participant-level condition table")
    st.dataframe(df[["participant_id", "assigned_group", "condition", "course_order", "word_count"]], use_container_width=True, hide_index=True)

elif page == "Review and Export":
    st.title("Review and Export")
    st.caption("Exports clearly identify the analysis as provisional or approved. Never overwrite earlier approved decisions without explicit researcher action.")

    st.subheader("Export options")
    if st.button("Export XLSX workbook"):
        workbook_path = EXPORT_DIR / "SPARK_Nudging_Interview_Analysis_Export.xlsx"
        export_workbook(state, workbook_path)
        st.success(f"XLSX exported to {workbook_path}")

    if st.button("Export coding CSV"):
        csv_path = EXPORT_DIR / "spark_nudging_coding.csv"
        export_coding_csv(state, csv_path)
        st.success(f"CSV exported to {csv_path}")

    if st.button("Export project JSON backup"):
        backup_path = write_project_backup(state)
        st.success(f"Project backup created at {backup_path}")

    if st.button("Export RQ findings report"):
        report_path = EXPORT_DIR / "rq_findings_report.md"
        export_rq_report(state, report_path)
        st.success(f"Findings report written to {report_path}")

    st.subheader("Audit log")
    st.dataframe(pd.DataFrame(state.get("audit_log", [])), use_container_width=True, hide_index=True)

    st.subheader("Analysis status")
    state["analysis_status"] = st.text_input("Current analysis status", state.get("analysis_status", "Provisional"))
    save_state(state)

# Global callouts
st.caption("Automated analysis is unavailable unless a researcher explicitly runs a model or import. AI suggestions remain provisional and must be reviewed.")

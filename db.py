from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from sample_case import (
    SAMPLE_AUDIT, SAMPLE_PROFILE, SAMPLE_METRICS, SAMPLE_PROBLEMS,
    SAMPLE_FINDINGS, SAMPLE_STRENGTHS, SAMPLE_ROADMAP,
)

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "data" / "velar.db"
PROBLEM_LIBRARY_PATH = BASE_DIR / "data" / "problem_library.json"
UPLOADS_DIR = BASE_DIR / "uploads"

STATUS_MULTIPLIERS = {
    "Confirmed": 1.0,
    "Suspected": 0.65,
    "Not Checked": 0.0,
    "Not Present": 0.0,
    "Not Applicable": 0.0,
}
EVIDENCE_MULTIPLIERS = {
    "Strong": 1.0,
    "Moderate": 0.8,
    "Weak": 0.6,
    "None": 0.4,
}
CRITICALITY_BONUS = {"Red": 8, "Yellow": 4, "Green": 0}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def init_database() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                audit_name TEXT NOT NULL,
                industry TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Draft',
                progress INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_profiles (
                audit_id INTEGER PRIMARY KEY,
                website TEXT NOT NULL DEFAULT '',
                market_geography TEXT NOT NULL DEFAULT '',
                auditor TEXT NOT NULL DEFAULT '',
                audit_start TEXT NOT NULL DEFAULT '',
                audit_end TEXT NOT NULL DEFAULT '',
                audit_version TEXT NOT NULL DEFAULT '1.0',
                business_model TEXT NOT NULL DEFAULT '',
                main_offer TEXT NOT NULL DEFAULT '',
                target_customer TEXT NOT NULL DEFAULT '',
                lead_sources TEXT NOT NULL DEFAULT '',
                sales_motion TEXT NOT NULL DEFAULT '',
                delivery_model TEXT NOT NULL DEFAULT '',
                team_size TEXT NOT NULL DEFAULT '',
                self_reported_constraint TEXT NOT NULL DEFAULT '',
                growth_goal TEXT NOT NULL DEFAULT '',
                marketing_data TEXT NOT NULL DEFAULT 'Partial',
                sales_data TEXT NOT NULL DEFAULT 'Partial',
                operations_data TEXT NOT NULL DEFAULT 'Partial',
                financial_data TEXT NOT NULL DEFAULT 'Partial',
                access_limitations TEXT NOT NULL DEFAULT '',
                audit_scope TEXT NOT NULL DEFAULT '',
                sensitive_data_notes TEXT NOT NULL DEFAULT '',
                executive_summary TEXT NOT NULL DEFAULT '',
                report_title TEXT NOT NULL DEFAULT 'Velar Efficiency Audit',
                FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS baseline_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_id INTEGER NOT NULL,
                metric TEXT NOT NULL,
                value TEXT NOT NULL DEFAULT '',
                unit_period TEXT NOT NULL DEFAULT '',
                source_notes TEXT NOT NULL DEFAULT '',
                UNIQUE(audit_id, metric),
                FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS problem_library (
                problem_id TEXT PRIMARY KEY,
                legacy_id TEXT,
                display_order INTEGER,
                flow_code TEXT,
                flow_en TEXT,
                flow_uk TEXT,
                group_id TEXT,
                group_en TEXT,
                group_uk TEXT,
                problem TEXT,
                problem_uk TEXT,
                simple_meaning TEXT,
                simple_meaning_uk TEXT,
                primary_type TEXT,
                pipe_logic TEXT,
                pipe_logic_uk TEXT,
                why_it_matters TEXT,
                why_it_matters_uk TEXT,
                symptoms TEXT,
                symptoms_uk TEXT,
                metrics_data_required TEXT,
                metrics_data_required_uk TEXT,
                first_diagnostic_question TEXT,
                first_diagnostic_question_uk TEXT,
                possible_fix_direction TEXT,
                possible_fix_direction_uk TEXT,
                base_criticality TEXT,
                criticality_rationale TEXT,
                criticality_rationale_uk TEXT,
                active TEXT,
                version TEXT,
                governance_notes TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_problems (
                audit_id INTEGER NOT NULL,
                problem_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Not Checked',
                evidence_strength TEXT NOT NULL DEFAULT 'None',
                revenue_impact INTEGER NOT NULL DEFAULT 1,
                flow_restriction INTEGER NOT NULL DEFAULT 1,
                urgency INTEGER NOT NULL DEFAULT 1,
                scale_risk INTEGER NOT NULL DEFAULT 1,
                confidence INTEGER NOT NULL DEFAULT 0,
                primary_constraint INTEGER NOT NULL DEFAULT 0,
                causal_role TEXT NOT NULL DEFAULT 'Unclassified',
                evidence_summary TEXT NOT NULL DEFAULT '',
                client_consequence TEXT NOT NULL DEFAULT '',
                recommendation TEXT NOT NULL DEFAULT '',
                effort TEXT NOT NULL DEFAULT 'M',
                dependency TEXT NOT NULL DEFAULT '',
                auditor_notes TEXT NOT NULL DEFAULT '',
                report_override TEXT NOT NULL DEFAULT 'Auto',
                updated_at TEXT NOT NULL,
                PRIMARY KEY (audit_id, problem_id),
                FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE,
                FOREIGN KEY (problem_id) REFERENCES problem_library(problem_id)
            );

            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_id INTEGER NOT NULL,
                problem_id TEXT NOT NULL,
                original_name TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                mime_type TEXT NOT NULL DEFAULT '',
                size_bytes INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE,
                FOREIGN KEY (problem_id) REFERENCES problem_library(problem_id)
            );

            CREATE TABLE IF NOT EXISTS findings (
                audit_id INTEGER NOT NULL,
                problem_id TEXT NOT NULL,
                rank INTEGER NOT NULL DEFAULT 1,
                owner TEXT NOT NULL DEFAULT '',
                target_date TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Not Started',
                PRIMARY KEY (audit_id, problem_id),
                FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE,
                FOREIGN KEY (problem_id) REFERENCES problem_library(problem_id)
            );

            CREATE TABLE IF NOT EXISTS strengths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                evidence TEXT NOT NULL DEFAULT '',
                preserve_guidance TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS roadmap_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_id INTEGER NOT NULL,
                phase TEXT NOT NULL,
                action TEXT NOT NULL,
                related_problem_ids TEXT NOT NULL DEFAULT '',
                expected_impact TEXT NOT NULL DEFAULT '',
                success_metric TEXT NOT NULL DEFAULT '',
                baseline TEXT NOT NULL DEFAULT '',
                target TEXT NOT NULL DEFAULT '',
                owner TEXT NOT NULL DEFAULT '',
                effort TEXT NOT NULL DEFAULT 'M',
                dependency TEXT NOT NULL DEFAULT '',
                target_date TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Not Started',
                notes TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE
            );
            """
        )
        con.commit()
    seed_problem_library()


def seed_problem_library() -> None:
    items = json.loads(PROBLEM_LIBRARY_PATH.read_text(encoding="utf-8"))
    mapping = {
        "Problem ID": "problem_id", "Legacy ID": "legacy_id", "Display Order": "display_order",
        "Flow Code": "flow_code", "Flow EN": "flow_en", "Flow UK": "flow_uk",
        "Group ID": "group_id", "Group EN": "group_en", "Group UK": "group_uk",
        "Problem": "problem", "Problem UK": "problem_uk",
        "Simple Meaning": "simple_meaning", "Simple Meaning UK": "simple_meaning_uk",
        "Primary Type": "primary_type", "Pipe Logic": "pipe_logic", "Pipe Logic UK": "pipe_logic_uk",
        "Why It Matters": "why_it_matters", "Why It Matters UK": "why_it_matters_uk",
        "Symptoms": "symptoms", "Symptoms UK": "symptoms_uk",
        "Metrics / Data Required": "metrics_data_required",
        "Metrics / Data Required UK": "metrics_data_required_uk",
        "First Diagnostic Question": "first_diagnostic_question",
        "First Diagnostic Question UK": "first_diagnostic_question_uk",
        "Possible Fix Direction": "possible_fix_direction",
        "Possible Fix Direction UK": "possible_fix_direction_uk",
        "Base Criticality": "base_criticality", "Criticality Rationale": "criticality_rationale",
        "Criticality Rationale UK": "criticality_rationale_uk", "Active": "active",
        "Version": "version", "Governance Notes": "governance_notes",
    }
    columns = list(mapping.values())
    placeholders = ",".join("?" for _ in columns)
    updates = ",".join(f"{column}=excluded.{column}" for column in columns if column != "problem_id")
    sql = (
        f"INSERT INTO problem_library ({','.join(columns)}) VALUES ({placeholders}) "
        f"ON CONFLICT(problem_id) DO UPDATE SET {updates}"
    )
    with get_connection() as con:
        for item in items:
            con.execute(sql, [item.get(source) for source in mapping])
        con.commit()


def initialize_audit_problem_rows(con: sqlite3.Connection, audit_id: int) -> None:
    timestamp = now_iso()
    con.execute(
        """
        INSERT OR IGNORE INTO audit_problems (audit_id, problem_id, updated_at)
        SELECT ?, problem_id, ? FROM problem_library WHERE active = 'Yes'
        """,
        (audit_id, timestamp),
    )


def create_audit(client_name: str, audit_name: str, industry: str = "") -> int:
    timestamp = now_iso()
    with get_connection() as con:
        cur = con.execute(
            """INSERT INTO audits
            (client_name, audit_name, industry, status, progress, created_at, updated_at)
            VALUES (?, ?, ?, 'Draft', 0, ?, ?)""",
            (client_name.strip(), audit_name.strip(), industry.strip(), timestamp, timestamp),
        )
        audit_id = int(cur.lastrowid)
        con.execute("INSERT INTO audit_profiles (audit_id) VALUES (?)", (audit_id,))
        initialize_default_metrics(con, audit_id)
        initialize_audit_problem_rows(con, audit_id)
        con.commit()
    return audit_id


def initialize_default_metrics(con: sqlite3.Connection, audit_id: int) -> None:
    metrics = [
        "Leads", "Lead → Customer Conversion", "Average Response Time", "Average Order Value",
        "Sales Cycle", "Team Capacity", "Revenue", "Gross Margin", "Net Margin",
        "Repeat Revenue Share", "Cash Reserve", "Owner Workload",
    ]
    con.executemany(
        "INSERT OR IGNORE INTO baseline_metrics (audit_id, metric) VALUES (?, ?)",
        [(audit_id, metric) for metric in metrics],
    )


def list_audits(search: str = "") -> list[dict[str, Any]]:
    sql = "SELECT * FROM audits"
    params: list[Any] = []
    if search:
        sql += " WHERE client_name LIKE ? OR audit_name LIKE ? OR industry LIKE ?"
        pattern = f"%{search}%"
        params = [pattern, pattern, pattern]
    sql += " ORDER BY updated_at DESC, id DESC"
    with get_connection() as con:
        rows = con.execute(sql, params).fetchall()
    return rows_to_dicts(rows)


def get_audit(audit_id: int) -> dict[str, Any] | None:
    with get_connection() as con:
        row = con.execute("SELECT * FROM audits WHERE id = ?", (audit_id,)).fetchone()
    return dict(row) if row else None


def delete_audit(audit_id: int) -> None:
    with get_connection() as con:
        con.execute("DELETE FROM audits WHERE id = ?", (audit_id,))
        con.commit()


def update_audit_header(audit_id: int, **fields: Any) -> None:
    allowed = {"client_name", "audit_name", "industry", "status", "progress"}
    safe = {k: v for k, v in fields.items() if k in allowed}
    if not safe:
        return
    safe["updated_at"] = now_iso()
    sets = ", ".join(f"{key} = ?" for key in safe)
    with get_connection() as con:
        con.execute(f"UPDATE audits SET {sets} WHERE id = ?", [*safe.values(), audit_id])
        con.commit()


def get_profile(audit_id: int) -> dict[str, Any]:
    with get_connection() as con:
        row = con.execute(
            """SELECT p.*, a.client_name, a.audit_name, a.industry
               FROM audit_profiles p JOIN audits a ON a.id = p.audit_id
               WHERE p.audit_id = ?""",
            (audit_id,),
        ).fetchone()
    return dict(row) if row else {}


def save_profile(audit_id: int, data: dict[str, Any]) -> None:
    profile_columns = {
        "website", "market_geography", "auditor", "audit_start", "audit_end", "audit_version",
        "business_model", "main_offer", "target_customer", "lead_sources", "sales_motion",
        "delivery_model", "team_size", "self_reported_constraint", "growth_goal", "marketing_data",
        "sales_data", "operations_data", "financial_data", "access_limitations", "audit_scope",
        "sensitive_data_notes", "executive_summary", "report_title",
    }
    profile = {k: str(v or "") for k, v in data.items() if k in profile_columns}
    header = {k: str(data[k] or "") for k in ("client_name", "audit_name", "industry") if k in data}
    with get_connection() as con:
        if profile:
            sets = ", ".join(f"{key} = ?" for key in profile)
            con.execute(f"UPDATE audit_profiles SET {sets} WHERE audit_id = ?", [*profile.values(), audit_id])
        if header:
            header["updated_at"] = now_iso()
            sets = ", ".join(f"{key} = ?" for key in header)
            con.execute(f"UPDATE audits SET {sets} WHERE id = ?", [*header.values(), audit_id])
        con.commit()
    recalculate_audit_progress(audit_id)


def get_metrics(audit_id: int) -> list[dict[str, Any]]:
    with get_connection() as con:
        rows = con.execute(
            "SELECT * FROM baseline_metrics WHERE audit_id = ? ORDER BY id", (audit_id,)
        ).fetchall()
    return rows_to_dicts(rows)


def save_metrics(audit_id: int, metrics: list[dict[str, Any]]) -> None:
    with get_connection() as con:
        for item in metrics:
            con.execute(
                """UPDATE baseline_metrics SET value = ?, unit_period = ?, source_notes = ?
                   WHERE audit_id = ? AND metric = ?""",
                (str(item.get("value", "")), str(item.get("unit_period", "")),
                 str(item.get("source_notes", "")), audit_id, item["metric"]),
            )
        con.commit()
    recalculate_audit_progress(audit_id)


def get_flow_options() -> list[str]:
    with get_connection() as con:
        rows = con.execute(
            "SELECT DISTINCT flow_en, MIN(display_order) ord FROM problem_library WHERE active='Yes' GROUP BY flow_en ORDER BY ord"
        ).fetchall()
    return [row[0] for row in rows]


def get_group_options(flow: str) -> list[tuple[str, str, str]]:
    with get_connection() as con:
        rows = con.execute(
            """SELECT DISTINCT group_id, group_en, group_uk, MIN(display_order) ord FROM problem_library
               WHERE active='Yes' AND flow_en=? GROUP BY group_id, group_en, group_uk ORDER BY ord""",
            (flow,),
        ).fetchall()
    return [(row[0], row[1], row[2]) for row in rows]


def list_audit_problems(
    audit_id: int,
    flow: str | None = None,
    group_id: str | None = None,
    status: str | None = None,
    search: str = "",
) -> list[dict[str, Any]]:
    sql = """
        SELECT l.*, ap.status, ap.evidence_strength, ap.revenue_impact, ap.flow_restriction,
               ap.urgency, ap.scale_risk, ap.confidence, ap.primary_constraint, ap.causal_role,
               ap.evidence_summary, ap.client_consequence, ap.recommendation, ap.effort,
               ap.dependency, ap.auditor_notes, ap.report_override
        FROM problem_library l
        JOIN audit_problems ap ON ap.problem_id = l.problem_id AND ap.audit_id = ?
        WHERE l.active = 'Yes'
    """
    params: list[Any] = [audit_id]
    if flow and flow != "All":
        sql += " AND l.flow_en = ?"
        params.append(flow)
    if group_id and group_id != "All":
        sql += " AND l.group_id = ?"
        params.append(group_id)
    if status and status != "All":
        sql += " AND ap.status = ?"
        params.append(status)
    if search:
        sql += " AND (l.problem LIKE ? OR l.problem_uk LIKE ? OR l.simple_meaning LIKE ? OR l.simple_meaning_uk LIKE ? OR l.problem_id LIKE ?)"
        pattern = f"%{search}%"
        params.extend([pattern, pattern, pattern, pattern, pattern])
    sql += " ORDER BY l.display_order"
    with get_connection() as con:
        rows = con.execute(sql, params).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item.update(calculate_problem_result(item))
        result.append(item)
    return result


def get_audit_problem(audit_id: int, problem_id: str) -> dict[str, Any] | None:
    rows = list_audit_problems(audit_id, search=problem_id)
    for row in rows:
        if row["problem_id"] == problem_id:
            return row
    return None


def calculate_problem_result(item: dict[str, Any]) -> dict[str, Any]:
    revenue = int(item.get("revenue_impact") or 1)
    flow = int(item.get("flow_restriction") or 1)
    urgency = int(item.get("urgency") or 1)
    scale = int(item.get("scale_risk") or 1)
    base = (revenue * 35 + flow * 30 + urgency * 20 + scale * 15) / 5
    bonus = (12 if int(item.get("primary_constraint") or 0) else 0) + CRITICALITY_BONUS.get(item.get("base_criticality"), 0)
    status_mult = STATUS_MULTIPLIERS.get(item.get("status"), 0)
    evidence_mult = EVIDENCE_MULTIPLIERS.get(item.get("evidence_strength"), 0.4)
    confidence = int(item.get("confidence") or 0) / 100
    score = min(100, round((base + bonus) * status_mult * evidence_mult * confidence))
    if score == 0:
        tier = "—"
    elif int(item.get("primary_constraint") or 0):
        tier = "P1 — Primary Constraint"
    elif item.get("primary_type") == "Revenue Leak" and score >= 65:
        tier = "P2 — Critical Revenue Leak"
    elif score >= 45:
        tier = "P3 — Bottleneck / Stability"
    else:
        tier = "P4 — Optimization / Monitor"
    override = item.get("report_override", "Auto")
    if override == "Include":
        include = True
    elif override == "Exclude":
        include = False
    else:
        include = bool(int(item.get("primary_constraint") or 0) or score >= 60)
    phase_map = {
        "P1 — Primary Constraint": "Phase 1 — Fix Primary Constraint",
        "P2 — Critical Revenue Leak": "Phase 2 — Stop Critical Leaks",
        "P3 — Bottleneck / Stability": "Phase 3 — Stabilize Operations",
        "P4 — Optimization / Monitor": "Phase 4 — Optimize & Scale",
    }
    return {"weighted_score": score, "priority_tier": tier, "include_in_report": include,
            "roadmap_phase": phase_map.get(tier, "—")}


def save_audit_problem(audit_id: int, problem_id: str, data: dict[str, Any]) -> None:
    allowed = {
        "status", "evidence_strength", "revenue_impact", "flow_restriction", "urgency", "scale_risk",
        "confidence", "primary_constraint", "causal_role", "evidence_summary", "client_consequence",
        "recommendation", "effort", "dependency", "auditor_notes", "report_override",
    }
    safe = {k: data[k] for k in data if k in allowed}
    safe["updated_at"] = now_iso()
    with get_connection() as con:
        if int(safe.get("primary_constraint", 0)):
            con.execute("UPDATE audit_problems SET primary_constraint = 0 WHERE audit_id = ?", (audit_id,))
        sets = ", ".join(f"{key} = ?" for key in safe)
        con.execute(
            f"UPDATE audit_problems SET {sets} WHERE audit_id = ? AND problem_id = ?",
            [*safe.values(), audit_id, problem_id],
        )
        con.execute("UPDATE audits SET status='In progress', updated_at=? WHERE id=?", (now_iso(), audit_id))
        con.commit()
    recalculate_audit_progress(audit_id)


def save_attachment(audit_id: int, problem_id: str, uploaded_file: Any) -> int:
    safe_name = Path(uploaded_file.name).name
    target_dir = UPLOADS_DIR / str(audit_id) / problem_id
    target_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{safe_name}"
    path = target_dir / stored_name
    data = uploaded_file.getbuffer()
    path.write_bytes(data)
    with get_connection() as con:
        cur = con.execute(
            """INSERT INTO attachments
            (audit_id, problem_id, original_name, stored_path, mime_type, size_bytes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (audit_id, problem_id, safe_name, str(path.relative_to(BASE_DIR)),
             getattr(uploaded_file, "type", "") or "", len(data), now_iso()),
        )
        con.commit()
        return int(cur.lastrowid)


def list_attachments(audit_id: int, problem_id: str) -> list[dict[str, Any]]:
    with get_connection() as con:
        rows = con.execute(
            "SELECT * FROM attachments WHERE audit_id=? AND problem_id=? ORDER BY created_at DESC",
            (audit_id, problem_id),
        ).fetchall()
    return rows_to_dicts(rows)


def delete_attachment(attachment_id: int) -> None:
    with get_connection() as con:
        row = con.execute("SELECT stored_path FROM attachments WHERE id=?", (attachment_id,)).fetchone()
        con.execute("DELETE FROM attachments WHERE id=?", (attachment_id,))
        con.commit()
    if row:
        path = BASE_DIR / row[0]
        if path.exists():
            path.unlink()


def get_attachment_bytes(attachment_id: int) -> tuple[str, bytes] | None:
    with get_connection() as con:
        row = con.execute("SELECT original_name, stored_path FROM attachments WHERE id=?", (attachment_id,)).fetchone()
    if not row:
        return None
    path = BASE_DIR / row[1]
    return (row[0], path.read_bytes()) if path.exists() else None


def get_primary_constraint(audit_id: int) -> dict[str, Any] | None:
    items = list_audit_problems(audit_id)
    for item in items:
        if int(item.get("primary_constraint") or 0):
            return item
    return None


def get_report_candidates(audit_id: int) -> list[dict[str, Any]]:
    items = list_audit_problems(audit_id)
    return [x for x in items if x["status"] in {"Confirmed", "Suspected"}]


def get_findings(audit_id: int) -> list[dict[str, Any]]:
    with get_connection() as con:
        rows = con.execute(
            """SELECT f.audit_id, f.problem_id, f.rank, f.owner, f.target_date, f.status AS finding_status,
                      l.problem, l.problem_uk, l.flow_en, l.flow_uk, l.group_en, l.group_uk, l.primary_type, l.base_criticality,
                      ap.status AS audit_status, ap.evidence_strength, ap.revenue_impact, ap.flow_restriction,
                      ap.urgency, ap.scale_risk, ap.confidence, ap.primary_constraint, ap.causal_role,
                      ap.evidence_summary, ap.client_consequence, ap.recommendation, ap.report_override
               FROM findings f
               JOIN problem_library l ON l.problem_id=f.problem_id
               JOIN audit_problems ap ON ap.audit_id=f.audit_id AND ap.problem_id=f.problem_id
               WHERE f.audit_id=? ORDER BY f.rank, l.display_order""",
            (audit_id,),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        # Scoring uses the diagnostic problem status. The finding's execution
        # status is kept separately for roadmap tracking.
        item["status"] = item.pop("audit_status")
        item.update(calculate_problem_result(item))
        result.append(item)
    return result


def save_findings(audit_id: int, problem_ids: list[str]) -> None:
    with get_connection() as con:
        existing = {row[0] for row in con.execute("SELECT problem_id FROM findings WHERE audit_id=?", (audit_id,))}
        selected = set(problem_ids)
        for problem_id in existing - selected:
            con.execute("DELETE FROM findings WHERE audit_id=? AND problem_id=?", (audit_id, problem_id))
        for rank, problem_id in enumerate(problem_ids, 1):
            con.execute(
                """INSERT INTO findings (audit_id, problem_id, rank)
                   VALUES (?, ?, ?)
                   ON CONFLICT(audit_id, problem_id) DO UPDATE SET rank=excluded.rank""",
                (audit_id, problem_id, rank),
            )
        con.commit()
    recalculate_audit_progress(audit_id)


def update_finding(audit_id: int, problem_id: str, rank: int, owner: str, target_date: str, status: str) -> None:
    with get_connection() as con:
        con.execute(
            """UPDATE findings SET rank=?, owner=?, target_date=?, status=?
               WHERE audit_id=? AND problem_id=?""",
            (rank, owner, target_date, status, audit_id, problem_id),
        )
        con.commit()


def list_strengths(audit_id: int) -> list[dict[str, Any]]:
    with get_connection() as con:
        rows = con.execute("SELECT * FROM strengths WHERE audit_id=? ORDER BY id", (audit_id,)).fetchall()
    return rows_to_dicts(rows)


def add_strength(audit_id: int, title: str, evidence: str, preserve_guidance: str) -> int:
    with get_connection() as con:
        cur = con.execute(
            "INSERT INTO strengths (audit_id,title,evidence,preserve_guidance,created_at) VALUES (?,?,?,?,?)",
            (audit_id, title, evidence, preserve_guidance, now_iso()),
        )
        con.commit()
        return int(cur.lastrowid)


def delete_strength(strength_id: int) -> None:
    with get_connection() as con:
        con.execute("DELETE FROM strengths WHERE id=?", (strength_id,))
        con.commit()


def list_roadmap_actions(audit_id: int) -> list[dict[str, Any]]:
    with get_connection() as con:
        rows = con.execute(
            """SELECT * FROM roadmap_actions WHERE audit_id=?
               ORDER BY CASE phase
                 WHEN 'Phase 1 — Fix Primary Constraint' THEN 1
                 WHEN 'Phase 2 — Stop Critical Leaks' THEN 2
                 WHEN 'Phase 3 — Stabilize Operations' THEN 3
                 ELSE 4 END, id""",
            (audit_id,),
        ).fetchall()
    return rows_to_dicts(rows)


def add_roadmap_action(audit_id: int, data: dict[str, Any]) -> int:
    fields = ["phase", "action", "related_problem_ids", "expected_impact", "success_metric",
              "baseline", "target", "owner", "effort", "dependency", "target_date", "status", "notes"]
    values = [str(data.get(field, "")) for field in fields]
    with get_connection() as con:
        cur = con.execute(
            f"INSERT INTO roadmap_actions (audit_id,{','.join(fields)}) VALUES (? ,{','.join('?' for _ in fields)})",
            [audit_id, *values],
        )
        con.commit()
        return int(cur.lastrowid)


def delete_roadmap_action(action_id: int) -> None:
    with get_connection() as con:
        con.execute("DELETE FROM roadmap_actions WHERE id=?", (action_id,))
        con.commit()


def update_roadmap_action(action_id: int, data: dict[str, Any]) -> None:
    allowed = {"phase", "action", "related_problem_ids", "expected_impact", "success_metric",
               "baseline", "target", "owner", "effort", "dependency", "target_date", "status", "notes"}
    safe = {k: str(v) for k, v in data.items() if k in allowed}
    if not safe:
        return
    with get_connection() as con:
        sets = ", ".join(f"{key}=?" for key in safe)
        con.execute(f"UPDATE roadmap_actions SET {sets} WHERE id=?", [*safe.values(), action_id])
        con.commit()


def dashboard_summary(audit_id: int) -> dict[str, Any]:
    items = list_audit_problems(audit_id)
    checked = sum(1 for x in items if x["status"] != "Not Checked")
    confirmed = sum(1 for x in items if x["status"] == "Confirmed")
    suspected = sum(1 for x in items if x["status"] == "Suspected")
    included = sum(1 for x in items if x["include_in_report"])
    evidence_covered = sum(1 for x in items if x["status"] == "Confirmed" and x["evidence_strength"] != "None")
    primary_count = sum(1 for x in items if int(x.get("primary_constraint") or 0))
    by_flow = []
    for flow in get_flow_options():
        subset = [x for x in items if x["flow_en"] == flow]
        flow_checked = sum(1 for x in subset if x["status"] != "Not Checked")
        max_score = max((x["weighted_score"] for x in subset), default=0)
        if flow_checked == 0:
            flow_status = "Not Assessed"
        elif max_score >= 60:
            flow_status = "Critical / High Priority"
        elif any(x["status"] in {"Confirmed", "Suspected"} for x in subset):
            flow_status = "At Risk"
        else:
            flow_status = "Stable / No Finding"
        by_flow.append({"flow": flow, "checked": flow_checked, "total": len(subset), "status": flow_status,
                        "max_score": max_score})
    return {
        "total": len(items), "checked": checked, "confirmed": confirmed, "suspected": suspected,
        "included": included, "primary_count": primary_count,
        "evidence_coverage": round((evidence_covered / confirmed) * 100) if confirmed else 100,
        "completeness": round((checked / len(items)) * 100) if items else 0,
        "by_flow": by_flow,
    }


def recalculate_audit_progress(audit_id: int) -> None:
    profile = get_profile(audit_id)
    profile_keys = ["business_model", "main_offer", "target_customer", "sales_motion", "delivery_model", "growth_goal"]
    profile_pct = sum(bool(profile.get(k)) for k in profile_keys) / len(profile_keys)
    summary = dashboard_summary(audit_id)
    diagnosis_pct = summary["checked"] / summary["total"] if summary["total"] else 0
    findings_pct = 1 if get_findings(audit_id) else 0
    roadmap_pct = 1 if list_roadmap_actions(audit_id) else 0
    progress = round(diagnosis_pct * 100)
    status = "Completed" if progress >= 100 and summary["primary_count"] == 1 else ("In progress" if progress > 0 else "Draft")
    update_audit_header(audit_id, progress=progress, status=status)


def create_sample_audit() -> int:
    """Create (or reopen) a synthetic sample case for demonstration."""
    with get_connection() as con:
        existing = con.execute(
            "SELECT id FROM audits WHERE audit_name = ? ORDER BY id LIMIT 1",
            (SAMPLE_AUDIT["audit_name"],),
        ).fetchone()
    if existing:
        return int(existing[0])

    audit_id = create_audit(
        SAMPLE_AUDIT["client_name"], SAMPLE_AUDIT["audit_name"], SAMPLE_AUDIT["industry"]
    )
    save_profile(audit_id, SAMPLE_PROFILE)

    metrics = get_metrics(audit_id)
    for metric in metrics:
        values = SAMPLE_METRICS.get(metric["metric"])
        if values:
            metric["value"], metric["unit_period"], metric["source_notes"] = values
    save_metrics(audit_id, metrics)

    for problem_id, values in SAMPLE_PROBLEMS.items():
        save_audit_problem(audit_id, problem_id, values)

    save_findings(audit_id, SAMPLE_FINDINGS)
    for title, evidence, preserve in SAMPLE_STRENGTHS:
        add_strength(audit_id, title, evidence, preserve)
    for action in SAMPLE_ROADMAP:
        add_roadmap_action(audit_id, action)

    recalculate_audit_progress(audit_id)
    return audit_id


# Backwards-compatible name for older local databases / imports.
def create_demo_audit() -> int:
    return create_sample_audit()

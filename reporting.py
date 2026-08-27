from __future__ import annotations

import csv
import html
import io
from collections import defaultdict
from typing import Any

import db

FLOW_LABELS = ["Marketing", "Sales", "Operations", "Finance", "Profit Output"]


def esc(value: Any) -> str:
    return html.escape(str(value or ""))


def flow_status_class(status: str) -> str:
    if "Critical" in status:
        return "critical"
    if status == "At Risk":
        return "risk"
    if status == "Stable / No Finding":
        return "stable"
    return "unknown"


def flow_status_label(status: str) -> str:
    """Short labels that remain legible inside compact flow-map nodes."""
    return {
        "Critical / High Priority": "Critical",
        "At Risk": "At risk",
        "Limited Assessment": "Limited",
        "Stable / No Finding": "Stable",
        "Not Assessed": "Not assessed",
    }.get(status, status)


def build_audit_register_csv(audit_id: int) -> bytes:
    items = db.list_audit_problems(audit_id)
    output = io.StringIO()
    fields = [
        "problem_id", "flow_en", "group_en", "problem", "primary_type", "base_criticality", "status",
        "evidence_strength", "revenue_impact", "flow_restriction", "urgency", "scale_risk", "confidence",
        "weighted_score", "priority_tier", "primary_constraint", "causal_role", "evidence_summary",
        "client_consequence", "recommendation", "effort", "dependency", "auditor_notes",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(items)
    return output.getvalue().encode("utf-8-sig")


def build_report_html(audit_id: int) -> str:
    audit = db.get_audit(audit_id) or {}
    profile = db.get_profile(audit_id)
    metrics = db.get_metrics(audit_id)
    summary = db.dashboard_summary(audit_id)
    primary = db.get_primary_constraint(audit_id)
    findings = db.get_findings(audit_id)
    strengths = db.list_strengths(audit_id)
    roadmap = db.list_roadmap_actions(audit_id)
    items = db.list_audit_problems(audit_id)

    metric_map = {m["metric"]: m for m in metrics if m.get("value")}
    confirmed_count = summary["confirmed"]
    checked_count = summary["checked"]
    flow_map = {row["flow"]: row for row in summary["by_flow"]}

    if not findings:
        findings = sorted(
            [x for x in items if x["include_in_report"]],
            key=lambda x: (-x["weighted_score"], x["display_order"]),
        )[:7]

    primary_title = primary["problem"] if primary else "Not selected"
    primary_flow = primary["flow_en"] if primary else "—"
    confidence = f"{primary['confidence']}%" if primary else "—"
    evidence_strength = primary["evidence_strength"] if primary else "—"

    pipe_nodes = []
    for flow in FLOW_LABELS:
        row = flow_map.get(flow, {"status": "Not Assessed", "checked": 0, "total": 0, "max_score": 0})
        cls = flow_status_class(row["status"])
        marker = "PRIMARY CONSTRAINT" if primary and primary["flow_en"] == flow else flow_status_label(row["status"])
        pipe_nodes.append(
            f"""
            <div class="pipe-node {cls} {'constraint-node' if primary and primary['flow_en']==flow else ''}">
              <div class="pipe-title">{esc(flow)}</div>
              <div class="pipe-status">{esc(marker)}</div>
              <div class="pipe-meta">{row['checked']}/{row['total']} checked · max score {row['max_score']}</div>
            </div>
            """
        )

    flow_profile_rows = []
    for flow in FLOW_LABELS:
        row = flow_map.get(flow, {"status": "Not Assessed", "max_score": 0})
        score = int(row.get("max_score") or 0)
        cls = flow_status_class(row.get("status", "Not Assessed"))
        flow_profile_rows.append(
            f"<div class='risk-row'><div class='risk-label'>{esc(flow)}</div><div class='risk-track'><div class='risk-fill {cls}' style='width:{score}%'></div></div><div class='risk-score'>{score}</div></div>"
        )
    flow_profile_html = "".join(flow_profile_rows)

    finding_cards = []
    for idx, finding in enumerate(findings, 1):
        finding_cards.append(
            f"""
            <article class="finding-card">
              <div class="finding-head">
                <div><span class="rank">{idx}</span><strong>{esc(finding['problem'])}</strong></div>
                <span class="pill">{esc(finding['priority_tier'])}</span>
              </div>
              <div class="finding-grid">
                <div><span class="label">Flow</span><b>{esc(finding['flow_en'])}</b></div>
                <div><span class="label">Type</span><b>{esc(finding['primary_type'])}</b></div>
                <div><span class="label">Score</span><b>{finding['weighted_score']}/100</b></div>
                <div><span class="label">Causal role</span><b>{esc(finding['causal_role'])}</b></div>
              </div>
              <div class="evidence"><span class="label">Evidence</span>{esc(finding['evidence_summary']) or 'Not documented'}</div>
              <div class="two-col">
                <div><span class="label">Business consequence</span>{esc(finding['client_consequence']) or 'Not documented'}</div>
                <div><span class="label">Solution direction</span>{esc(finding['recommendation']) or 'Not documented'}</div>
              </div>
            </article>
            """
        )

    root_causes = [f for f in findings if f.get("causal_role") == "Root Cause"]
    contributing = [f for f in findings if f.get("causal_role") == "Contributing Cause"]
    symptoms = [f for f in findings if f.get("causal_role") == "Symptom"]
    causal_columns = []
    for label, group, cls in [
        ("Root cause", root_causes, "root"),
        ("Contributing causes", contributing, "contrib"),
        ("Observed symptoms", symptoms, "symptom"),
    ]:
        content = "".join(f"<div class='chain-item'>{esc(x['problem'])}</div>" for x in group) or "<div class='chain-empty'>Not classified</div>"
        causal_columns.append(f"<div class='chain-stage {cls}'><span class='label'>{label}</span>{content}</div>")
    consequence_text = primary.get("client_consequence", "") if primary else ""
    causal_columns.append(f"<div class='chain-stage outcome'><span class='label'>Business effect</span><div class='chain-item'>{esc(consequence_text) or 'Not documented'}</div></div>")
    causal_chain_html = "<div class='causal-chain'>" + "<div class='chain-arrow'>→</div>".join(causal_columns) + "</div>"

    strengths_html = "".join(
        f"""
        <div class="strength-card">
          <strong>{esc(s['title'])}</strong>
          <p>{esc(s['evidence'])}</p>
          <small>Protect: {esc(s['preserve_guidance'])}</small>
        </div>
        """ for s in strengths
    ) or '<div class="empty">No protected strengths selected yet.</div>'

    roadmap_by_phase: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for action in roadmap:
        roadmap_by_phase[action["phase"]].append(action)

    roadmap_html_parts = []
    for phase in [
        "Phase 1 — Fix Primary Constraint", "Phase 2 — Stop Critical Leaks",
        "Phase 3 — Stabilize Operations", "Phase 4 — Optimize & Scale",
    ]:
        actions = roadmap_by_phase.get(phase, [])
        if not actions:
            continue
        rows = "".join(
            f"""
            <tr>
              <td>{esc(a['action'])}</td><td>{esc(a['related_problem_ids'])}</td>
              <td>{esc(a['success_metric'])}</td><td>{esc(a['baseline'])}</td>
              <td>{esc(a['target'])}</td><td>{esc(a['owner'])}</td><td>{esc(a['effort'])}</td>
            </tr>
            """ for a in actions
        )
        roadmap_html_parts.append(
            f"""
            <h3>{esc(phase)}</h3>
            <table class="roadmap-table"><thead><tr>
              <th>Action</th><th>Related issues</th><th>Metric</th><th>Baseline</th><th>Target</th><th>Owner</th><th>Effort</th>
            </tr></thead><tbody>{rows}</tbody></table>
            """
        )
    roadmap_html = "".join(roadmap_html_parts) or '<div class="empty">Roadmap has not been created yet.</div>'

    primary_proof = ""
    if primary:
        proof_points = [
            f"Status is {primary['status'].lower()} with {primary['evidence_strength'].lower()} evidence.",
            f"Auditor confidence is {primary['confidence']}% and weighted severity is {primary['weighted_score']}/100.",
            f"Its causal role is classified as {primary['causal_role']} rather than a standalone symptom.",
            "It was selected as the single constraint that best explains the current downstream business result.",
        ]
        primary_proof = "".join(f"<li>{esc(p)}</li>" for p in proof_points)

    metric_cards = []
    for key in ["Leads", "Lead → Customer Conversion", "Average Response Time", "Revenue", "Gross Margin", "Net Margin"]:
        metric = metric_map.get(key)
        if metric:
            metric_cards.append(
                f"<div class='metric-card'><span>{esc(key)}</span><b>{esc(metric['value'])}</b><small>{esc(metric['unit_period'])}</small></div>"
            )
    metric_cards_html = "".join(metric_cards) or "<div class='empty'>Baseline metrics are not filled yet.</div>"

    register_rows = []
    for item in items:
        if item["status"] == "Not Checked":
            continue
        register_rows.append(
            f"<tr><td>{esc(item['problem_id'])}</td><td>{esc(item['flow_en'])}</td><td>{esc(item['problem'])}</td>"
            f"<td>{esc(item['status'])}</td><td>{esc(item['evidence_strength'])}</td><td>{item['weighted_score']}</td>"
            f"<td>{esc(item['causal_role'])}</td><td>{esc(item['client_consequence'])}</td></tr>"
        )
    register_html = "".join(register_rows) or "<tr><td colspan='8'>No problems have been checked yet.</td></tr>"

    executive_summary = profile.get("executive_summary") or (
        f"The audit reviewed {checked_count} of {summary['total']} diagnostic hypotheses and confirmed {confirmed_count} issues. "
        f"The current primary constraint is {primary_title}."
    )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(profile.get('report_title') or 'Velar Efficiency Audit')} — {esc(audit.get('client_name'))}</title>
<style>
:root{{--ink:#151a1a;--muted:#667070;--line:#dde4e3;--soft:#f4f8f7;--teal:#0f8f8c;--red:#ba3c45;--amber:#b97810;--green:#2b7d5a}}
*{{box-sizing:border-box}} body{{margin:0;background:#eef2f1;color:var(--ink);font-family:Inter,Arial,sans-serif;line-height:1.45}}
.report{{max-width:1120px;margin:24px auto;background:white;box-shadow:0 14px 45px #18302c18}}
.page{{padding:42px 48px;border:1px solid var(--line);margin:0 0 18px;border-radius:16px;min-height:auto;background:white}}
.page:last-child{{margin-bottom:0}} .eyebrow{{letter-spacing:.16em;font-size:12px;font-weight:800;color:var(--teal)}}
h1{{font-size:42px;line-height:1.08;margin:20px 0 12px}} h2{{font-size:27px;margin:0 0 18px}} h3{{margin-top:26px}}
p{{color:#3f4948}} .cover{{display:flex;flex-direction:column;justify-content:space-between;background:linear-gradient(135deg,#f8fbfb 55%,#e0f2f0)}}
.cover-meta{{display:grid;grid-template-columns:1fr 1fr;gap:20px;border-top:1px solid var(--line);padding-top:24px}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}} .metric-card{{padding:16px;border:1px solid var(--line);border-radius:12px;background:var(--soft)}}
.metric-card span,.label{{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:5px}}
.metric-card b{{font-size:22px}} .metric-card small{{display:block;color:var(--muted);margin-top:4px}}
.pipe{{display:flex;align-items:stretch;gap:11px;margin:28px 0}} .pipe-node{{flex:1;position:relative;padding:18px 12px;border:2px solid var(--line);border-radius:14px;text-align:center}}
.pipe-node:not(:last-child):after{{content:'→';position:absolute;right:-19px;top:42%;color:#86918f;font-size:22px;z-index:2}}
.pipe-node.critical{{border-color:#e7a3a8;background:#fff4f4}} .pipe-node.risk{{border-color:#e7c080;background:#fff9ec}}
.pipe-node.stable{{border-color:#9fd1ba;background:#f2fbf6}} .pipe-node.constraint-node{{box-shadow:0 0 0 4px #ba3c4514}}
.pipe-title{{font-weight:800}} .pipe-status{{font-size:11px;color:var(--muted);margin:8px 0}} .pipe-meta{{font-size:10px;color:#7f8988}}
.risk-profile{{margin-top:28px;border:1px solid var(--line);border-radius:14px;padding:18px;background:#fbfcfc}} .risk-row{{display:grid;grid-template-columns:120px 1fr 34px;gap:12px;align-items:center;margin:11px 0}} .risk-label{{font-size:12px;font-weight:700}} .risk-track{{height:9px;background:#e8eeee;border-radius:999px;overflow:hidden}} .risk-fill{{height:100%;background:#b6c2c0}} .risk-fill.critical{{background:var(--red)}} .risk-fill.risk{{background:var(--amber)}} .risk-fill.stable{{background:var(--green)}} .risk-score{{font-size:11px;color:var(--muted);text-align:right}}
.causal-chain{{display:grid;grid-template-columns:1fr auto 1fr auto 1fr auto 1fr;gap:10px;align-items:stretch;margin-top:26px}} .chain-stage{{border:1px solid var(--line);border-radius:14px;padding:17px;background:#fbfcfc;min-height:150px}} .chain-stage.root{{border-color:#e4b6ba;background:#fff8f8}} .chain-stage.contrib{{border-color:#ead3a7;background:#fffaf1}} .chain-stage.symptom{{border-color:#cbd8d6}} .chain-stage.outcome{{border-color:#acd7c3;background:#f5fbf7}} .chain-item{{font-size:12px;font-weight:650;margin:8px 0;padding:8px;border-radius:8px;background:white;border:1px solid #edf0f0}} .chain-empty{{font-size:12px;color:var(--muted);margin-top:10px}} .chain-arrow{{display:grid;place-items:center;color:#87918f;font-size:22px}}
.primary-box{{display:grid;grid-template-columns:1.1fr 1fr;gap:22px;padding:24px;border:1px solid #e5a8ad;border-radius:16px;background:#fff7f7}}
.primary-title{{font-size:24px;font-weight:800}} ul{{padding-left:20px}} li{{margin:7px 0}}
.finding-card{{border:1px solid var(--line);border-radius:15px;padding:22px;margin:15px 0;page-break-inside:avoid}}
.finding-head{{display:flex;justify-content:space-between;gap:10px;align-items:center}} .rank{{display:inline-grid;place-items:center;width:28px;height:28px;border-radius:50%;background:var(--ink);color:white;margin-right:10px}}
.pill{{font-size:11px;padding:5px 8px;background:var(--soft);border-radius:999px}} .finding-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0}}
.evidence{{background:var(--soft);padding:14px;border-radius:10px}} .two-col{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}}
.strength-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}} .strength-card{{border:1px solid #b8dcca;border-radius:14px;padding:18px;background:#f5fcf8}}
.roadmap-table,.register{{width:100%;border-collapse:collapse;font-size:12px}} th,td{{padding:9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}} th{{color:var(--muted);font-size:10px;text-transform:uppercase}}
.empty{{padding:20px;border:1px dashed var(--line);color:var(--muted);border-radius:12px}}
.scope-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}} .scope-card{{border:1px solid var(--line);padding:18px;border-radius:14px;break-inside:avoid;page-break-inside:avoid}}

@media(max-width:800px){{.page{{padding:28px}}.grid,.finding-grid,.strength-grid{{grid-template-columns:1fr 1fr}}.pipe{{flex-direction:column}}.pipe-node:after{{display:none}}.primary-box,.two-col,.scope-grid,.causal-chain{{grid-template-columns:1fr}}.chain-arrow{{transform:rotate(90deg)}}}}
</style></head><body><main class="report">
<section class="page cover"><div><div class="eyebrow">VELAR · DIAGNOSTIC STANDARD</div><h1>{esc(profile.get('report_title') or 'Velar Efficiency Audit')}</h1><p style="font-size:20px">{esc(audit.get('client_name'))}</p></div>
<div class="cover-meta"><div><span class="label">Audit</span>{esc(audit.get('audit_name'))}</div><div><span class="label">Prepared by</span>{esc(profile.get('auditor') or 'Velar')}</div><div><span class="label">Market</span>{esc(profile.get('market_geography'))}</div><div><span class="label">Version</span>{esc(profile.get('audit_version'))}</div></div></section>
<section class="page"><div class="eyebrow">01 · EXECUTIVE SUMMARY</div><h2>What currently limits the business flow</h2><p style="font-size:18px">{esc(executive_summary)}</p>
<div class="grid">{metric_cards_html}</div><h3>Diagnostic result</h3><div class="grid"><div class="metric-card"><span>Primary flow</span><b>{esc(primary_flow)}</b></div><div class="metric-card"><span>Primary constraint</span><b style="font-size:17px">{esc(primary_title)}</b></div><div class="metric-card"><span>Checked</span><b>{checked_count}/{summary['total']}</b></div><div class="metric-card"><span>Confirmed findings with evidence</span><b>{summary['evidence_coverage']}%</b></div></div></section>
<section class="page"><div class="eyebrow">02 · REVENUE FLOW MAP</div><h2>Where the flow slows, leaks or becomes unstable</h2><div class="pipe">{''.join(pipe_nodes)}</div><div class="risk-profile"><span class="label">Flow risk profile · maximum weighted score by flow</span>{flow_profile_html}</div>
<div class="scope-grid" style="margin-top:24px"><div class="scope-card"><span class="label">Business model</span>{esc(profile.get('business_model'))}<br><br><span class="label">Main offer</span>{esc(profile.get('main_offer'))}<br><br><span class="label">Target customer</span>{esc(profile.get('target_customer'))}</div><div class="scope-card"><span class="label">Audit scope</span>{esc(profile.get('audit_scope'))}<br><br><span class="label">Access limitations</span>{esc(profile.get('access_limitations'))}</div></div></section>
<section class="page"><div class="eyebrow">03 · PRIMARY CONSTRAINT CASE</div><h2>Why this issue was selected first</h2><div class="primary-box"><div><span class="label">Primary constraint</span><div class="primary-title">{esc(primary_title)}</div><p>{esc(primary.get('simple_meaning') if primary else '')}</p><span class="label">Evidence summary</span><p>{esc(primary.get('evidence_summary') if primary else 'Not selected')}</p><span class="label">Business consequence</span><p>{esc(primary.get('client_consequence') if primary else '')}</p></div><div><span class="label">Why we are confident</span><ul>{primary_proof or '<li>Primary constraint has not been selected.</li>'}</ul><div class="grid" style="grid-template-columns:1fr 1fr"><div class="metric-card"><span>Confidence</span><b>{esc(confidence)}</b></div><div class="metric-card"><span>Evidence</span><b>{esc(evidence_strength)}</b></div></div></div></div></section>
<section class="page"><div class="eyebrow">04 · CAUSAL CHAIN</div><h2>How the diagnosed issues connect to the business result</h2><p>The chain is assembled from the auditor’s causal-role classification. It is not generated by AI.</p>{causal_chain_html}</section>
<section class="page"><div class="eyebrow">05 · KEY FINDINGS</div><h2>The few issues that explain the largest business effect</h2>{''.join(finding_cards) or '<div class="empty">No findings selected.</div>'}</section>
<section class="page"><div class="eyebrow">06 · PROTECTED STRENGTHS</div><h2>What already works and must not be broken</h2><div class="strength-grid">{strengths_html}</div></section>
<section class="page"><div class="eyebrow">07 · OPTIMIZATION ROADMAP</div><h2>What to change, in what order, and how success will be measured</h2>{roadmap_html}</section>
<section class="page"><div class="eyebrow">APPENDIX · AUDIT REGISTER</div><h2>All reviewed diagnostic hypotheses</h2><table class="register"><thead><tr><th>ID</th><th>Flow</th><th>Problem</th><th>Status</th><th>Evidence</th><th>Score</th><th>Causal role</th><th>Consequence</th></tr></thead><tbody>{register_html}</tbody></table></section>
</main></body></html>"""


def _pdf_safe(value: Any) -> str:
    text = str(value or "")
    for old, new in {
        "→": "->", "≤": "<=", "≥": ">=", "—": "-", "–": "-",
        "“": '"', "”": '"', "’": "'", "·": " | ", "×": "x", "™": "",
    }.items():
        text = text.replace(old, new)
    return " ".join(text.split())


def build_report_pdf(audit_id: int) -> bytes:
    """Create the final English client report directly as PDF.

    This avoids browser print headers, local file paths and browser-dependent page breaks.
    """
    from reportlab.graphics.shapes import Drawing, Line, Rect, String
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from pathlib import Path
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        BaseDocTemplate, Frame, KeepTogether, PageBreak, PageTemplate,
        Paragraph, Spacer, Table, TableStyle,
    )

    audit = db.get_audit(audit_id) or {}
    profile = db.get_profile(audit_id)
    metrics = db.get_metrics(audit_id)
    summary = db.dashboard_summary(audit_id)
    primary = db.get_primary_constraint(audit_id)
    findings = db.get_findings(audit_id)
    strengths = db.list_strengths(audit_id)
    roadmap = db.list_roadmap_actions(audit_id)
    items = db.list_audit_problems(audit_id)

    if not findings:
        findings = sorted(
            [x for x in items if x["include_in_report"]],
            key=lambda x: (-x["weighted_score"], x["display_order"]),
        )[:7]

    buf = io.BytesIO()
    page_w, page_h = A4
    left = right = 17 * mm
    top = 17 * mm
    bottom = 17 * mm
    usable_w = page_w - left - right

    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=left, rightMargin=right, topMargin=top, bottomMargin=bottom,
        title=_pdf_safe(profile.get("report_title") or "Velar Efficiency Audit"),
        author="Velar",
    )
    frame = Frame(left, bottom, usable_w, page_h - top - bottom, id="main")

    # Use local system fonts when available. Nothing is bundled with the project.
    regular_font = "Helvetica"
    bold_font = "Helvetica-Bold"
    font_candidates = [
        (Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/arialbd.ttf")),
        (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
    ]
    for regular_path, bold_path in font_candidates:
        if regular_path.exists() and bold_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("VelarSans", str(regular_path)))
                pdfmetrics.registerFont(TTFont("VelarSansBold", str(bold_path)))
                regular_font = "VelarSans"
                bold_font = "VelarSansBold"
                break
            except Exception:
                pass

    teal = colors.HexColor("#0F8F8C")
    deep_teal = colors.HexColor("#0B6F6D")
    ink = colors.HexColor("#171B1B")
    muted = colors.HexColor("#687271")
    line = colors.HexColor("#DCE5E3")
    soft = colors.HexColor("#F4F8F7")
    mint = colors.HexColor("#E9F5F3")
    red = colors.HexColor("#BB454C")
    amber = colors.HexColor("#B57B18")
    green = colors.HexColor("#287E59")

    def footer(canvas, report_doc):
        canvas.saveState()
        if report_doc.page == 1:
            canvas.setFillColor(mint)
            canvas.rect(0, 0, page_w, page_h, stroke=0, fill=1)
            canvas.setFillColor(deep_teal)
            canvas.rect(0, page_h - 4 * mm, page_w, 4 * mm, stroke=0, fill=1)
        else:
            canvas.setFillColor(colors.HexColor("#FBFCFC"))
            canvas.rect(0, 0, page_w, page_h, stroke=0, fill=1)
            canvas.setFillColor(teal)
            canvas.rect(0, page_h - 2.2 * mm, page_w, 2.2 * mm, stroke=0, fill=1)
        canvas.setStrokeColor(line)
        canvas.line(left, 11 * mm, page_w - right, 11 * mm)
        canvas.setFont(regular_font, 7)
        canvas.setFillColor(muted)
        canvas.drawString(left, 6.8 * mm, "VELAR | Diagnostic Report | Confidential")
        canvas.drawRightString(page_w - right, 6.8 * mm, f"Page {report_doc.page}")
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=footer)])

    styles = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=styles["Title"], fontName=bold_font, fontSize=29, leading=33, textColor=ink, spaceAfter=8)
    H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName=bold_font, fontSize=18, leading=22, textColor=ink, spaceBefore=2, spaceAfter=12)
    H3 = ParagraphStyle("H3", parent=styles["Heading3"], fontName=bold_font, fontSize=11.5, leading=14, textColor=ink, spaceBefore=7, spaceAfter=5)
    BODY = ParagraphStyle("BODY", parent=styles["BodyText"], fontName=regular_font, fontSize=9.2, leading=12.8, textColor=colors.HexColor("#414B4A"), spaceAfter=6)
    SMALL = ParagraphStyle("SMALL", parent=BODY, fontSize=7.2, leading=9.4, textColor=muted)
    LABEL = ParagraphStyle("LABEL", parent=SMALL, fontName=bold_font, fontSize=6.7, leading=8.5, textColor=muted, spaceAfter=2)
    SCORE = ParagraphStyle("SCORE", parent=H3, alignment=TA_CENTER)
    WHITE = ParagraphStyle("WHITE", parent=BODY, fontName=bold_font, textColor=colors.white, alignment=TA_CENTER)
    EYEBROW = ParagraphStyle("EYEBROW", parent=LABEL, textColor=teal, fontSize=7.6, leading=10)
    COVER_H1 = ParagraphStyle("COVER_H1", parent=H1, alignment=0, fontSize=31, leading=35, spaceBefore=0, spaceAfter=10)
    COVER_CLIENT = ParagraphStyle("COVER_CLIENT", parent=BODY, alignment=0, fontSize=13, leading=17, textColor=ink, spaceAfter=0)
    COVER_VALUE = ParagraphStyle("COVER_VALUE", parent=BODY, fontName=bold_font, fontSize=10, leading=13, textColor=ink, spaceAfter=0)

    def P(value: Any, style=BODY) -> Paragraph:
        return Paragraph(html.escape(_pdf_safe(value)), style)

    def section(number: str, title: str) -> list:
        return [P(number, EYEBROW), P(title, H2)]

    story = []

    # Cover
    story += [Spacer(1, 15 * mm), P("VELAR | DIAGNOSTIC STANDARD", EYEBROW),
              Spacer(1, 4 * mm),
              P(profile.get("report_title") or "Velar Efficiency Audit", COVER_H1),
              P(audit.get("client_name"), COVER_CLIENT),
              Spacer(1, 7 * mm)]
    story += [Table([[""]], colWidths=[usable_w], rowHeights=[0.7], style=[("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#C7DEDA"))]), Spacer(1, 9 * mm)]

    def cover_field(label: str, value: Any) -> list:
        return [P(label, LABEL), Spacer(1, 1.5 * mm), P(value or "-", COVER_VALUE)]

    cover = Table([
        [cover_field("AUDIT", audit.get("audit_name")), cover_field("PREPARED BY", profile.get("auditor") or "Velar")],
        [cover_field("MARKET", profile.get("market_geography") or "-"), cover_field("VERSION", profile.get("audit_version") or "1.0")],
    ], colWidths=[usable_w/2]*2)
    cover.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),colors.white),("BOX",(0,0),(-1,-1),0.7,colors.HexColor("#C7DEDA")),
        ("INNERGRID",(0,0),(-1,-1),0.45,colors.HexColor("#D6E7E4")),
        ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12),
        ("TOPPADDING",(0,0),(-1,-1),11),("BOTTOMPADDING",(0,0),(-1,-1),11),
    ]))
    story += [cover, Spacer(1, 24 * mm),
              P("Evidence-led diagnosis | Prioritized constraints | Actionable roadmap", ParagraphStyle("COVER_TAG", parent=SMALL, textColor=deep_teal, fontSize=8.2, leading=11)),
              PageBreak()]

    # Executive summary
    story += section("01 | EXECUTIVE SUMMARY", "What currently limits the business flow")
    primary_title = primary["problem"] if primary else "Not selected"
    executive = profile.get("executive_summary") or (
        f"The audit reviewed {summary['checked']} of {summary['total']} diagnostic hypotheses and confirmed {summary['confirmed']} issues. "
        f"The current primary constraint is {primary_title}."
    )
    story += [P(executive, ParagraphStyle("LEAD", parent=BODY, fontSize=11.2, leading=15.5, textColor=ink)), Spacer(1, 3*mm)]

    metric_map = {m["metric"]: m for m in metrics if m.get("value")}
    metric_keys = ["Leads", "Lead → Customer Conversion", "Average Response Time", "Revenue"]
    cells = []
    for key in metric_keys:
        m = metric_map.get(key)
        value = m["value"] if m else "-"
        unit = m["unit_period"] if m else ""
        cells.append([P(key, LABEL), P(value, ParagraphStyle("MVAL", parent=BODY, fontName=bold_font, fontSize=13.5, leading=16, textColor=ink)), P(unit, SMALL)])
    metrics_table = Table([cells], colWidths=[usable_w/4]*4)
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),soft),("BOX",(0,0),(-1,-1),0.5,line),("INNERGRID",(0,0),(-1,-1),0.35,line),
        ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
        ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),
    ]))
    story += [metrics_table, Spacer(1, 5*mm)]
    result = Table([
        [P("PRIMARY FLOW", LABEL), P("PRIMARY CONSTRAINT", LABEL), P("CHECKED", LABEL), P("CONFIRMED FINDINGS WITH EVIDENCE", LABEL)],
        [P(primary["flow_en"] if primary else "-", H3), P(primary_title, H3), P(f"{summary['checked']}/{summary['total']}", H3), P(f"{summary['evidence_coverage']}%", H3)],
    ], colWidths=[usable_w/4]*4)
    result.setStyle(TableStyle([
        ("BOX",(0,0),(-1,-1),0.5,line),("INNERGRID",(0,0),(-1,-1),0.35,line),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),
    ]))
    story += [result, PageBreak()]

    # Revenue flow map
    story += section("02 | REVENUE FLOW MAP", "Where the flow slows, leaks or becomes unstable")
    flow_map = {row["flow"]: row for row in summary["by_flow"]}
    drawing = Drawing(usable_w, 67)
    node_w = 89
    gap = (usable_w - node_w*5) / 4
    y = 18
    for idx, flow in enumerate(FLOW_LABELS):
        row = flow_map.get(flow, {"status":"Not Assessed","checked":0,"total":0,"max_score":0})
        x = idx * (node_w + gap)
        status = row["status"]
        border, fill = line, colors.white
        if "Critical" in status: border, fill = red, colors.HexColor("#FFF5F5")
        elif status == "At Risk": border, fill = amber, colors.HexColor("#FFFAF0")
        elif status == "Stable / No Finding": border, fill = green, colors.HexColor("#F4FBF7")
        if primary and primary["flow_en"] == flow: border = red
        drawing.add(Rect(x, y, node_w, 40, 7, strokeColor=border, fillColor=fill, strokeWidth=1.1))
        drawing.add(String(x+node_w/2, y+26, _pdf_safe(flow), fontName=bold_font, fontSize=7.5, textAnchor="middle", fillColor=ink))
        marker = "PRIMARY" if primary and primary["flow_en"] == flow else flow_status_label(status)
        drawing.add(String(x+node_w/2, y+14, marker, fontName=regular_font, fontSize=5.4, textAnchor="middle", fillColor=muted))
        drawing.add(String(x+node_w/2, y+5, f"{row['checked']}/{row['total']} | score {row['max_score']}", fontName=regular_font, fontSize=5.2, textAnchor="middle", fillColor=muted))
        if idx < 4:
            x1, x2 = x+node_w+2, x+node_w+gap-2
            drawing.add(Line(x1, y+20, x2, y+20, strokeColor=muted, strokeWidth=.7))
            drawing.add(Line(x2-4, y+23, x2, y+20, strokeColor=muted, strokeWidth=.7))
            drawing.add(Line(x2-4, y+17, x2, y+20, strokeColor=muted, strokeWidth=.7))
    story += [drawing, Spacer(1, 3*mm), P("Flow risk profile", H3)]

    risk = Drawing(usable_w, 108)
    for idx, flow in enumerate(FLOW_LABELS):
        row = flow_map.get(flow, {"status":"Not Assessed","max_score":0})
        score = int(row.get("max_score") or 0)
        yy = 88 - idx*20
        risk.add(String(0, yy, _pdf_safe(flow), fontName=bold_font, fontSize=7.2, fillColor=ink))
        risk.add(Rect(88, yy-2, usable_w-122, 7, 3, strokeColor=None, fillColor=colors.HexColor("#EDF1F0")))
        bar = colors.HexColor("#B9C4C2")
        if "Critical" in row.get("status", ""): bar = red
        elif row.get("status") == "At Risk": bar = amber
        elif row.get("status") == "Stable / No Finding": bar = green
        risk.add(Rect(88, yy-2, (usable_w-122)*score/100, 7, 3, strokeColor=None, fillColor=bar))
        risk.add(String(usable_w-24, yy, str(score), fontName=regular_font, fontSize=7, fillColor=muted))
    story += [risk, Spacer(1, 3*mm)]

    context = Table([
        [P("BUSINESS MODEL", LABEL), P("AUDIT SCOPE", LABEL)],
        [P(profile.get("business_model") or "-"), P(profile.get("audit_scope") or "-")],
        [P("MAIN OFFER", LABEL), P("ACCESS LIMITATIONS", LABEL)],
        [P(profile.get("main_offer") or "-"), P(profile.get("access_limitations") or "-")],
        [P("TARGET CUSTOMER", LABEL), P("", LABEL)],
        [P(profile.get("target_customer") or "-"), P("", BODY)],
    ], colWidths=[usable_w/2]*2)
    context.setStyle(TableStyle([
        ("BOX",(0,0),(-1,-1),0.5,line),("INNERGRID",(0,0),(-1,-1),0.3,line),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    story += [context, PageBreak()]

    # Primary constraint and causal chain
    story += section("03 | PRIMARY CONSTRAINT", "Why this issue is addressed first")
    if primary:
        story += [P(primary["problem"], ParagraphStyle("PT", parent=H1, fontSize=21, leading=25)), P(primary.get("simple_meaning"), BODY)]
        primary_table = Table([
            [P("EVIDENCE", LABEL), P("BUSINESS CONSEQUENCE", LABEL)],
            [P(primary.get("evidence_summary") or "Not documented"), P(primary.get("client_consequence") or "Not documented")],
            [P("CONFIDENCE", LABEL), P("DECISION BASIS", LABEL)],
            [P(f"{primary['confidence']}% | {primary['evidence_strength']} evidence | {primary['weighted_score']}/100"), P(f"Causal role: {primary['causal_role']}. The auditor selected this as the single Primary Constraint.")],
        ], colWidths=[usable_w/2]*2)
        primary_table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#FFF8F8")),("BOX",(0,0),(-1,-1),0.7,colors.HexColor("#E5A1A7")),
            ("INNERGRID",(0,0),(-1,-1),0.35,line),("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),
        ]))
        story += [primary_table]
    else:
        story += [P("Primary constraint has not been selected.")]

    story += [Spacer(1, 6*mm), P("Causal chain", H3)]
    roots = [f["problem"] for f in findings if f.get("causal_role") == "Root Cause"]
    contrib = [f["problem"] for f in findings if f.get("causal_role") == "Contributing Cause"]
    symptoms = [f["problem"] for f in findings if f.get("causal_role") == "Symptom"]
    chain = Table([
        [P("ROOT CAUSE", LABEL), P("CONTRIBUTING CAUSES", LABEL), P("OBSERVED SYMPTOMS", LABEL), P("BUSINESS EFFECT", LABEL)],
        [P("; ".join(roots) or "Not classified"), P("; ".join(contrib) or "Not classified"), P("; ".join(symptoms) or "Not classified"), P(primary.get("client_consequence") if primary else "Not documented")],
    ], colWidths=[usable_w/4]*4)
    chain.setStyle(TableStyle([
        ("BOX",(0,0),(-1,-1),0.5,line),("INNERGRID",(0,0),(-1,-1),0.35,line),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#FFF7F7")),("BACKGROUND",(1,0),(1,-1),colors.HexColor("#FFFAF2")),("BACKGROUND",(3,0),(3,-1),colors.HexColor("#F4FBF7")),
        ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    story += [chain, PageBreak()]

    # Key findings
    story += section("04 | KEY FINDINGS", "The issues that explain the largest business effect")
    if not findings:
        story += [P("No findings selected.")]
    for idx, finding in enumerate(findings, 1):
        header = Table([[P(str(idx), WHITE), P(finding["problem"], H3), P(f"{finding['weighted_score']}/100", SCORE)]], colWidths=[12*mm, usable_w-34*mm, 22*mm])
        header.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(0,0),ink),("BOX",(0,0),(-1,-1),0.5,line),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
        ]))
        detail = Table([
            [P("FLOW", LABEL), P("TYPE", LABEL), P("CAUSAL ROLE", LABEL), P("EVIDENCE", LABEL)],
            [P(finding["flow_en"]), P(finding["primary_type"]), P(finding["causal_role"]), P(finding["evidence_strength"])],
            [P("EVIDENCE SUMMARY", LABEL), P("BUSINESS CONSEQUENCE", LABEL), P("SOLUTION DIRECTION", LABEL), P("PRIORITY", LABEL)],
            [P(finding.get("evidence_summary") or "Not documented"), P(finding.get("client_consequence") or "Not documented"), P(finding.get("recommendation") or "Not documented"), P(finding.get("priority_tier") or "-")],
        ], colWidths=[usable_w/4]*4)
        detail.setStyle(TableStyle([
            ("BOX",(0,0),(-1,-1),0.5,line),("INNERGRID",(0,0),(-1,-1),0.3,line),("VALIGN",(0,0),(-1,-1),"TOP"),
            ("BACKGROUND",(0,0),(-1,0),soft),("BACKGROUND",(0,2),(-1,2),soft),
            ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ]))
        story += [KeepTogether([header, detail]), Spacer(1, 4*mm)]
    story += [PageBreak()]

    # Protected strengths
    story += section("05 | PROTECTED STRENGTHS", "What already works and should not be broken")
    if strengths:
        rows = [[P("STRENGTH", LABEL), P("EVIDENCE", LABEL), P("PRESERVE", LABEL)]]
        for s in strengths:
            rows.append([P(s["title"]), P(s["evidence"]), P(s["preserve_guidance"])])
        table = Table(rows, colWidths=[usable_w*.24, usable_w*.42, usable_w*.34], repeatRows=1)
        table.setStyle(TableStyle([
            ("BOX",(0,0),(-1,-1),0.5,line),("INNERGRID",(0,0),(-1,-1),0.3,line),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#F4FBF7")),
            ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),
        ]))
        story += [table]
    else:
        story += [P("No protected strengths selected yet.")]
    story += [PageBreak()]

    # Roadmap
    story += section("06 | OPTIMIZATION ROADMAP", "What to change, in what order, and how success will be measured")
    by_phase: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for action in roadmap:
        by_phase[action["phase"]].append(action)
    has_actions = False
    for phase in ["Phase 1 — Fix Primary Constraint", "Phase 2 — Stop Critical Leaks", "Phase 3 — Stabilize Operations", "Phase 4 — Optimize & Scale"]:
        actions = by_phase.get(phase, [])
        if not actions:
            continue
        has_actions = True
        for action_index, a in enumerate(actions):
            meta = Table([
                [P("RELATED ISSUES", LABEL), P("OWNER", LABEL), P("EFFORT", LABEL), P("TARGET DATE", LABEL), P("STATUS", LABEL)],
                [P(a["related_problem_ids"] or "-", SMALL), P(a["owner"] or "-", SMALL),
                 P(a["effort"] or "-", SMALL), P(a["target_date"] or "-", SMALL), P(a["status"] or "Not Started", SMALL)],
            ], colWidths=[usable_w*.30, usable_w*.20, usable_w*.10, usable_w*.20, usable_w*.20])
            meta.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),soft),("BOX",(0,0),(-1,-1),0.45,line),("INNERGRID",(0,0),(-1,-1),0.25,line),
                ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
                ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ]))
            measures = Table([
                [P("SUCCESS METRIC", LABEL), P("BASELINE", LABEL), P("TARGET", LABEL)],
                [P(a["success_metric"] or "-", SMALL), P(a["baseline"] or "-", SMALL), P(a["target"] or "-", SMALL)],
            ], colWidths=[usable_w*.34, usable_w*.33, usable_w*.33])
            measures.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),soft),("BOX",(0,0),(-1,-1),0.45,line),("INNERGRID",(0,0),(-1,-1),0.25,line),
                ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
                ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ]))
            action_block = [
                P(a["action"], H3), meta, Spacer(1, 2*mm),
                P("EXPECTED IMPACT", LABEL), P(a["expected_impact"] or "Not documented", SMALL),
                measures,
            ]
            if action_index == 0:
                # Keep a phase heading with its first action instead of leaving
                # the heading orphaned at the bottom of a page.
                action_block.insert(0, P(phase, H3))
            if a.get("dependency"):
                action_block += [Spacer(1, 1.5*mm), P("DEPENDENCY", LABEL), P(a["dependency"], SMALL)]
            if a.get("notes"):
                action_block += [P("NOTES / SCOPE", LABEL), P(a["notes"], SMALL)]
            story += [KeepTogether(action_block), Spacer(1, 5*mm)]
    if not has_actions:
        story += [P("Roadmap has not been created yet.")]
    story += [PageBreak()]

    # Audit register
    story += section("APPENDIX | AUDIT REGISTER", "Reviewed diagnostic hypotheses")
    checked = [x for x in items if x["status"] != "Not Checked"]
    rows = [[P("ID", LABEL),P("FLOW", LABEL),P("PROBLEM", LABEL),P("STATUS", LABEL),P("EVIDENCE", LABEL),P("SCORE", LABEL),P("ROLE", LABEL)]]
    for x in checked:
        rows.append([P(x["problem_id"], SMALL),P(x["flow_en"], SMALL),P(x["problem"], SMALL),P(x["status"], SMALL),P(x["evidence_strength"], SMALL),P(x["weighted_score"], SMALL),P(x["causal_role"], SMALL)])
    if len(rows) == 1:
        rows.append([P("-", SMALL),P("-", SMALL),P("No problems have been checked yet.", SMALL),P("-", SMALL),P("-", SMALL),P("-", SMALL),P("-", SMALL)])
    register = Table(rows, colWidths=[usable_w*.07,usable_w*.11,usable_w*.34,usable_w*.13,usable_w*.12,usable_w*.08,usable_w*.15], repeatRows=1)
    register.setStyle(TableStyle([
        ("BOX",(0,0),(-1,-1),0.45,line),("INNERGRID",(0,0),(-1,-1),0.25,line),("BACKGROUND",(0,0),(-1,0),soft),
        ("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]))
    story += [register]

    doc.build(story)
    return buf.getvalue()

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

import db
from i18n import localize_problem, localize_value, tr
from reporting import build_audit_register_csv, build_report_html, build_report_pdf

st.set_page_config(page_title="Velar Diagnostic App", page_icon="V", layout="wide", initial_sidebar_state="expanded")
db.init_database()

STATUS_OPTIONS = ["Not Checked", "Not Present", "Suspected", "Confirmed", "Not Applicable"]
EVIDENCE_OPTIONS = ["None", "Weak", "Moderate", "Strong"]
CONFIDENCE_OPTIONS = [0, 25, 50, 75, 100]
CAUSAL_OPTIONS = ["Unclassified", "Root Cause", "Contributing Cause", "Symptom", "Standalone"]
EFFORT_OPTIONS = ["XS", "S", "M", "L", "XL"]
OVERRIDE_OPTIONS = ["Auto", "Include", "Exclude"]
EXECUTION_STATUS = ["Not Started", "In Progress", "Blocked", "Done", "Deferred"]
PHASE_OPTIONS = [
    "Phase 1 — Fix Primary Constraint", "Phase 2 — Stop Critical Leaks",
    "Phase 3 — Stabilize Operations", "Phase 4 — Optimize & Scale",
]

st.markdown(
    """
    <style>
    :root { --velar:#0f8f8c; --ink:#171b1b; --muted:#6c7574; --line:#dbe3e2; --input:#aebcba; --soft:#f5f8f7; }
    .stApp { background:#f6f8f7; }
    .block-container { max-width:1380px; padding-top:1.8rem; padding-bottom:3rem; }
    [data-testid="stSidebar"] { background:#ffffff; border-right:1px solid var(--line); }
    [data-testid="stSidebar"] .block-container { padding-top:1.1rem; }
    h1,h2,h3 { color:var(--ink); letter-spacing:-.02em; }
    .brand { font-weight:900; letter-spacing:.18em; font-size:1.08rem; }
    .brand-sub { color:var(--muted); font-size:.78rem; margin-top:.2rem; }
    .page-kicker { color:var(--velar); font-weight:800; letter-spacing:.09em; font-size:.73rem; text-transform:uppercase; }
    .muted { color:var(--muted); }
    .badge { display:inline-flex; padding:.26rem .55rem; border-radius:999px; background:#e9f7f6; color:#087875; font-size:.73rem; font-weight:800; }
    .success-badge { background:#eef9f3; color:#287e59; }
    .problem-title { font-weight:800; font-size:1.18rem; margin-bottom:.3rem; }
    .flow-card { padding:.8rem; border:1px solid var(--line); border-radius:12px; background:white; }
    .flow-card.critical { border-color:#e8aeb3; background:#fff7f7; }
    .flow-card.risk { border-color:#ecd09d; background:#fffbf1; }
    .flow-card.stable { border-color:#add7c2; background:#f4fbf7; }
    div[data-testid="stForm"], div[data-testid="stExpander"] { background:white; border-color:var(--line); }
    .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button { border-radius:9px; }
    .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] { background:var(--velar); border-color:var(--velar); }
    [data-testid="stMetric"] { background:white; border:1px solid var(--line); padding:.8rem 1rem; border-radius:12px; }

    /* Inputs must be visible before focus. */
    .stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input {
        background:#ffffff !important; border:1.5px solid var(--input) !important;
        border-radius:9px !important; box-shadow:0 1px 2px rgba(20,45,42,.05) !important;
    }
    div[data-baseweb="select"] > div, div[data-baseweb="base-input"] {
        background:#ffffff !important; border-color:var(--input) !important;
        box-shadow:0 1px 2px rgba(20,45,42,.05) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus, .stDateInput input:focus {
        border-color:var(--velar) !important; box-shadow:0 0 0 2px rgba(15,143,140,.14) !important;
    }
    input::placeholder, textarea::placeholder { color:#929e9c !important; opacity:1 !important; }

    /* Remove Streamlit keyboard instruction under focused text areas. */
    [data-testid="InputInstructions"], div[data-testid="InputInstructions"],
    .stTextArea [data-testid="InputInstructions"], .stTextInput [data-testid="InputInstructions"] { display:none !important; }

    /* Keep Streamlit chrome out of the application surface. */
    [data-testid="stToolbar"], #MainMenu, footer { display:none !important; }
    .proto-badge { display:inline-block; margin-top:.45rem; padding:.18rem .45rem; border:1px solid var(--line); border-radius:999px; color:var(--muted); font-size:.67rem; }
    .lang-caption { color:var(--muted); font-size:.68rem; text-align:center; margin-bottom:.18rem; }

    </style>
    """,
    unsafe_allow_html=True,
)


def ensure_state() -> None:
    st.session_state.setdefault("page", "Audits")
    st.session_state.setdefault("selected_audit_id", None)
    st.session_state.setdefault("new_audit_open", False)
    st.session_state.setdefault("selected_problem_id", None)
    st.session_state.setdefault("language", "en")


ensure_state()


def lang() -> str:
    return st.session_state.language


def L(key: str, **kwargs) -> str:
    return tr(key, lang(), **kwargs)


def V(value) -> str:
    return localize_value(value, lang())


def navigate(page: str, audit_id: int | None = None) -> None:
    if audit_id is not None:
        st.session_state.selected_audit_id = int(audit_id)
    st.session_state.page = page
    st.rerun()


def selected_audit() -> dict | None:
    audit_id = st.session_state.selected_audit_id
    return db.get_audit(int(audit_id)) if audit_id else None


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f'<div class="brand">VELAR</div><div class="brand-sub">{L("DIAGNOSTIC WORKSPACE")}</div><span class="proto-badge">{L("Prototype v0.4")}</span>', unsafe_allow_html=True)
        st.write("")
        if st.button(L("Audits"), use_container_width=True, type="primary" if st.session_state.page == "Audits" else "secondary"):
            navigate("Audits")
        audit = selected_audit()
        if audit:
            st.caption(L("OPEN AUDIT · #{id}", id=audit['id']))
            st.markdown(f"**{audit['client_name']}**")
            st.caption(audit["audit_name"])
            for page in ["Overview", "Profile", "Diagnosis", "Findings", "Report"]:
                if st.button(L(page), key=f"nav_{page}", use_container_width=True, type="primary" if st.session_state.page == page else "secondary"):
                    navigate(page)
            st.divider()
            st.progress(int(audit["progress"]))
            st.caption(L("{progress}% complete · {status}", progress=audit['progress'], status=V(audit['status'])))
        else:
            st.info(L("Open or create an audit to see the workspace."))


def render_language_switch() -> None:
    st.markdown(f'<div class="lang-caption">{L("Language")}</div>', unsafe_allow_html=True)
    en_col, uk_col = st.columns(2, gap="small")
    if en_col.button("EN", key=f"lang_en_{st.session_state.page}", help="English",
                     type="primary" if lang() == "en" else "secondary", use_container_width=True):
        if lang() != "en":
            st.session_state.language = "en"
            st.rerun()
    if uk_col.button("UA", key=f"lang_uk_{st.session_state.page}", help="Українська",
                     type="primary" if lang() == "uk" else "secondary", use_container_width=True):
        if lang() != "uk":
            st.session_state.language = "uk"
            st.rerun()


def page_header(kicker: str, title: str, subtitle: str = "") -> None:
    left, right = st.columns([8.4, 1.6], vertical_alignment="top")
    with left:
        st.markdown(f'<div class="page-kicker">{L(kicker)}</div>', unsafe_allow_html=True)
        st.title(L(title))
        if subtitle:
            st.markdown(f'<div class="muted">{L(subtitle)}</div>', unsafe_allow_html=True)
    with right:
        render_language_switch()
    st.write("")


def require_audit() -> dict:
    audit = selected_audit()
    if audit is None:
        st.warning(L("Choose an audit first."))
        if st.button(L("Back to audits")):
            navigate("Audits")
        st.stop()
    return audit


def render_audits_page() -> None:
    page_header("Workspace", "Audits", "Create a new audit or continue an existing case.")
    top_left, top_right = st.columns([4, 1])
    with top_right:
        if st.button(L("+ New Audit"), type="primary", use_container_width=True):
            st.session_state.new_audit_open = not st.session_state.new_audit_open
    if st.session_state.new_audit_open:
        with st.form("new_audit_form", clear_on_submit=True):
            st.subheader(L("Create audit"))
            c1, c2, c3 = st.columns(3)
            client = c1.text_input(L("Client / Company *"))
            audit_name = c2.text_input(L("Audit name"))
            industry = c3.text_input(L("Industry"))
            create = st.form_submit_button(L("Create and open"), type="primary")
            if create:
                if not client.strip():
                    st.error(L("Client name is required."))
                else:
                    audit_id = db.create_audit(client, audit_name or f"{client} — Velar Efficiency Audit", industry)
                    st.session_state.new_audit_open = False
                    navigate("Profile", audit_id)
    search = st.text_input(L("Search audits"), placeholder=L("Client, audit name or industry"), label_visibility="collapsed")
    audits = db.list_audits(search)
    if not audits:
        st.info(L("No audits yet. Create the first one."))
        return
    for audit in audits:
        with st.container(border=True):
            left, progress_col, status_col, open_col, menu_col = st.columns([4.5, 2, 1.3, 1, .65], vertical_alignment="center")
            with left:
                st.markdown(f"### {audit['client_name']}")
                st.caption(f"{audit['audit_name']} · {audit['industry'] or L('Industry not specified')}")
            with progress_col:
                st.caption(L("Progress")); st.progress(int(audit["progress"])); st.caption(f"{audit['progress']}%")
            with status_col:
                status_class = "success-badge" if audit["status"] == "Completed" else "badge"
                st.markdown(f'<span class="{status_class}">{V(audit["status"])}</span>', unsafe_allow_html=True)
                st.caption(audit["updated_at"].replace("T", " ")[:16])
            with open_col:
                if st.button(L("Open"), key=f"open_{audit['id']}", type="primary", use_container_width=True):
                    navigate("Overview", audit["id"])
            with menu_col:
                with st.popover("•••"):
                    if st.button(L("Delete audit"), key=f"delete_{audit['id']}"):
                        db.delete_audit(int(audit["id"]))
                        if st.session_state.selected_audit_id == audit["id"]:
                            st.session_state.selected_audit_id = None
                        st.rerun()


def render_overview_page() -> None:
    audit = require_audit(); summary = db.dashboard_summary(audit["id"]); primary = db.get_primary_constraint(audit["id"])
    page_header("Audit overview", audit["client_name"], audit["audit_name"])
    cols = st.columns(5)
    values = [("Checked", f"{summary['checked']}/{summary['total']}"),("Confirmed",summary["confirmed"]),("Suspected",summary["suspected"]),("Report findings",summary["included"]),("Evidence coverage",f"{summary['evidence_coverage']}%")]
    for col,(label,value) in zip(cols,values): col.metric(L(label),value)
    st.subheader(L("Revenue Flow")); flow_cols=st.columns(5)
    for col,row in zip(flow_cols,summary["by_flow"]):
        cls="critical" if "Critical" in row["status"] else ("risk" if row["status"]=="At Risk" else ("stable" if row["status"]=="Stable / No Finding" else ""))
        col.markdown(f'<div class="flow-card {cls}"><b>{V(row["flow"])}</b><br><small>{V(row["status"])}</small><br><small>{L("{checked}/{total} checked",checked=row["checked"],total=row["total"])}</small></div>',unsafe_allow_html=True)
    st.write(""); left,right=st.columns([1.2,1])
    with left:
        st.subheader(L("Primary constraint"))
        if primary:
            p=localize_problem(primary,lang())
            with st.container(border=True):
                st.markdown(f"### {p['problem']}"); st.caption(f"{p['flow_en']} · {V(p['priority_tier'])} · {L('Score {score}',score=p['weighted_score'])}")
                st.write(p["client_consequence"] or p["simple_meaning"])
                if st.button(L("Open in diagnosis")):
                    st.session_state.selected_problem_id=p["problem_id"]; navigate("Diagnosis")
        else: st.warning(L("Primary constraint has not been selected."))
    with right:
        st.subheader(L("Quality control"))
        checks=[(summary["primary_count"]==1,"Exactly one primary constraint"),(summary["evidence_coverage"]==100,"Evidence coverage for confirmed findings"),(3<=len(db.get_findings(audit["id"]))<=10,"3–10 key findings selected"),(bool(db.list_roadmap_actions(audit["id"])),"Roadmap contains actions")]
        for ok,label in checks: st.write(("✅" if ok else "⬜")+" "+L(label))
    with st.expander(L("How this prototype works")):
        st.write("• " + L("Scores are rule-based and come from the auditor’s assessment — not AI."))
        st.write("• " + L("Attachments are stored as evidence; the prototype does not automatically read or analyze them."))
        st.write("• " + L("The auditor selects one Primary Constraint after reviewing evidence and causal roles."))
        st.write("• " + L("The report is assembled from the profile, selected findings, strengths and roadmap actions."))


def render_profile_page() -> None:
    audit=require_audit(); profile=db.get_profile(audit["id"]); metrics=db.get_metrics(audit["id"])
    page_header("Step 1","Client Profile","Business context, baseline metrics, data availability and audit scope.")
    tab1,tab2,tab3=st.tabs([L("Business context"),L("Baseline metrics"),L("Data & scope")])
    with tab1:
        # One deliberate vertical flow: no two-column business context.
        outer_left, center, outer_right = st.columns([1, 3.4, 1])
        with center:
            with st.form("profile_business"):
                client_name=st.text_input(L("Client / Company"),value=profile.get("client_name",""))
                audit_name=st.text_input(L("Audit name"),value=profile.get("audit_name",""))
                website=st.text_input(L("Website"),value=profile.get("website",""))
                industry=st.text_input(L("Industry"),value=profile.get("industry",""))
                market=st.text_input(L("Market / Geography"),value=profile.get("market_geography",""))
                auditor=st.text_input(L("Auditor"),value=profile.get("auditor",""))
                business_model=st.text_area(L("Business model"),value=profile.get("business_model",""),height=78)
                main_offer=st.text_area(L("Main offer"),value=profile.get("main_offer",""),height=78)
                target_customer=st.text_area(L("Target customer"),value=profile.get("target_customer",""),height=78)
                lead_sources=st.text_area(L("Lead sources"),value=profile.get("lead_sources",""),height=78)
                sales_motion=st.text_area(L("Sales motion"),value=profile.get("sales_motion",""),height=78)
                delivery_model=st.text_area(L("Delivery model"),value=profile.get("delivery_model",""),height=78)
                team_size=st.text_input(L("Team size"),value=profile.get("team_size",""))
                self_constraint=st.text_input(L("Self-reported constraint"),value=profile.get("self_reported_constraint",""))
                growth_goal=st.text_input(L("Growth goal"),value=profile.get("growth_goal",""))
                if st.form_submit_button(L("Save business context"),type="primary"):
                    db.save_profile(audit["id"],{"client_name":client_name,"audit_name":audit_name,"website":website,"industry":industry,"market_geography":market,"auditor":auditor,"business_model":business_model,"main_offer":main_offer,"target_customer":target_customer,"lead_sources":lead_sources,"sales_motion":sales_motion,"delivery_model":delivery_model,"team_size":team_size,"self_reported_constraint":self_constraint,"growth_goal":growth_goal})
                    st.success(L("Business context saved."))
    with tab2:
        st.caption(L("Do not invent values. Add source and period for every metric you use in the report.")); edited=[]
        with st.form("metrics_form"):
            for metric in metrics:
                c1,c2,c3,c4=st.columns([2.2,1.3,1.5,3]); c1.markdown(f"**{V(metric['metric'])}**")
                value=c2.text_input(L("Value"),value=metric["value"],key=f"mv_{metric['id']}",label_visibility="collapsed")
                unit=c3.text_input(L("Unit / period"),value=metric["unit_period"],key=f"mu_{metric['id']}",label_visibility="collapsed")
                notes=c4.text_input(L("Source / notes"),value=metric["source_notes"],key=f"mn_{metric['id']}",label_visibility="collapsed")
                edited.append({"metric":metric["metric"],"value":value,"unit_period":unit,"source_notes":notes})
            if st.form_submit_button(L("Save metrics"),type="primary"): db.save_metrics(audit["id"],edited); st.success(L("Metrics saved."))
    with tab3:
        with st.form("scope_form"):
            c1,c2,c3,c4=st.columns(4); availability=["Yes","Partial","No"]
            fmt=lambda x:V(x)
            marketing_data=c1.selectbox(L("Marketing data"),availability,index=availability.index(profile.get("marketing_data","Partial")),format_func=fmt)
            sales_data=c2.selectbox(L("CRM / Sales data"),availability,index=availability.index(profile.get("sales_data","Partial")),format_func=fmt)
            operations_data=c3.selectbox(L("Operations data"),availability,index=availability.index(profile.get("operations_data","Partial")),format_func=fmt)
            financial_data=c4.selectbox(L("Financial data"),availability,index=availability.index(profile.get("financial_data","Partial")),format_func=fmt)
            access=st.text_area(L("Access limitations"),value=profile.get("access_limitations","")); scope=st.text_area(L("Audit scope / exclusions"),value=profile.get("audit_scope","")); sensitive=st.text_area(L("Sensitive data handling notes"),value=profile.get("sensitive_data_notes",""))
            report_title=st.text_input(L("Report title (English)"),value=profile.get("report_title","Velar Efficiency Audit")); executive=st.text_area(L("Executive summary draft (English)"),value=profile.get("executive_summary",""),height=140)
            if st.form_submit_button(L("Save data & scope"),type="primary"):
                db.save_profile(audit["id"],{"marketing_data":marketing_data,"sales_data":sales_data,"operations_data":operations_data,"financial_data":financial_data,"access_limitations":access,"audit_scope":scope,"sensitive_data_notes":sensitive,"report_title":report_title,"executive_summary":executive}); st.success(L("Scope saved."))


def render_diagnosis_page() -> None:
    audit=require_audit(); page_header("Step 2","Diagnosis","Review the problem library, document evidence and determine the primary constraint.")
    with st.container(border=True):
        f1,f2,f3,f4=st.columns([1.3,1.8,1.3,2.2]); flows=["All"]+db.get_flow_options(); flow=f1.selectbox(L("Flow"),flows,format_func=lambda x:V(x))
        raw_groups=db.get_group_options(flow) if flow!="All" else []; groups=[("All","All groups","Усі групи")]+raw_groups
        group_labels={gid:(uk if lang()=="uk" else en) for gid,en,uk in groups}; group_id=f2.selectbox(L("Group"),[x[0] for x in groups],format_func=lambda x:group_labels[x])
        status_filter=f3.selectbox(L("Status"),["All"]+STATUS_OPTIONS,format_func=lambda x:V(x)); search=f4.text_input(L("Search"),placeholder=L("Problem, meaning or ID"))
    problems=db.list_audit_problems(audit["id"],flow=flow,group_id=group_id,status=status_filter,search=search)
    localized={p["problem_id"]:localize_problem(p,lang()) for p in problems}
    if not problems: st.info(L("No problems match the filters.")); return
    option_ids=[p["problem_id"] for p in problems]; current=st.session_state.selected_problem_id
    if current not in option_ids: current=option_ids[0]
    selected_id=st.selectbox(L("Problems ({count})",count=len(problems)),option_ids,index=option_ids.index(current),format_func=lambda pid:f"{pid} · {localized[pid]['problem']} · {V(localized[pid]['status'])} · {L('Score {score}',score=localized[pid]['weighted_score'])}")
    st.session_state.selected_problem_id=selected_id; raw=db.get_audit_problem(audit["id"],selected_id)
    if not raw:return
    problem=localize_problem(raw,lang()); left,right=st.columns([1.05,1.5])
    with left:
        with st.container(border=True):
            st.markdown(f'<div class="problem-title">{problem["problem"]}</div>',unsafe_allow_html=True); st.caption(f"{problem['problem_id']} · {problem['flow_en']} / {problem['group_en']}")
            st.write(problem["simple_meaning"]); st.markdown(f"**{L('Why it matters')}**"); st.write(problem["why_it_matters"])
            with st.expander(L("Symptoms")): st.write(problem["symptoms"])
            with st.expander(L("Metrics / data required")): st.write(problem["metrics_data_required"])
            st.info(problem["first_diagnostic_question"])
            with st.expander(L("Library solution direction")): st.write(problem["possible_fix_direction"])
            st.caption(L("Base criticality: {criticality} · {type}",criticality=V(problem['base_criticality']),type=V(problem['primary_type'])))
        st.subheader(L("Filtered problem register")); table=[]
        for p in problems:
            lp=localized[p["problem_id"]]; table.append({"ID":p["problem_id"],L("Problem"):lp["problem"],L("Status"):V(p["status"]),L("Evidence"):V(p["evidence_strength"]),L("Score {score}",score=""):p["weighted_score"],L("Tier"):V(p["priority_tier"])})
        st.dataframe(table,use_container_width=True,hide_index=True,height=360)
    with right:
        with st.form(f"problem_form_{selected_id}"):
            st.subheader(L("Client-specific assessment")); c1,c2,c3=st.columns(3)
            status=c1.selectbox(L("Status"),STATUS_OPTIONS,index=STATUS_OPTIONS.index(raw["status"]),format_func=lambda x:V(x)); evidence_strength=c2.selectbox(L("Evidence strength"),EVIDENCE_OPTIONS,index=EVIDENCE_OPTIONS.index(raw["evidence_strength"]),format_func=lambda x:V(x)); causal_role=c3.selectbox(L("Causal role"),CAUSAL_OPTIONS,index=CAUSAL_OPTIONS.index(raw["causal_role"]),format_func=lambda x:V(x))
            s1,s2,s3,s4,s5=st.columns(5); revenue=s1.slider(L("Revenue"),1,5,int(raw["revenue_impact"])); restriction=s2.slider(L("Flow"),1,5,int(raw["flow_restriction"])); urgency=s3.slider(L("Urgency"),1,5,int(raw["urgency"])); scale=s4.slider(L("Scale risk"),1,5,int(raw["scale_risk"])); confidence=s5.select_slider(L("Confidence"),CONFIDENCE_OPTIONS,value=int(raw["confidence"]),format_func=lambda x:f"{x}%")
            c4,c5,c6=st.columns(3); primary=c4.checkbox(L("Primary constraint"),value=bool(raw["primary_constraint"])); effort=c5.selectbox(L("Effort"),EFFORT_OPTIONS,index=EFFORT_OPTIONS.index(raw["effort"])); override=c6.selectbox(L("Report override"),OVERRIDE_OPTIONS,index=OVERRIDE_OPTIONS.index(raw["report_override"]),format_func=lambda x:V(x))
            evidence_summary=st.text_area(L("Evidence summary"),value=raw["evidence_summary"],height=105); consequence=st.text_area(L("Client consequence"),value=raw["client_consequence"],height=95); recommendation=st.text_area(L("Client-specific recommendation"),value=raw["recommendation"],height=95); dependency=st.text_input(L("Dependency"),value=raw["dependency"]); notes=st.text_area(L("Auditor notes"),value=raw["auditor_notes"],height=80)
            if st.form_submit_button(L("Save assessment"),type="primary"):
                if status=="Confirmed" and evidence_strength=="None": st.error(L("Confirmed findings require evidence strength and a documented source."))
                else:
                    db.save_audit_problem(audit["id"],selected_id,{"status":status,"evidence_strength":evidence_strength,"revenue_impact":revenue,"flow_restriction":restriction,"urgency":urgency,"scale_risk":scale,"confidence":confidence,"primary_constraint":int(primary),"causal_role":causal_role,"evidence_summary":evidence_summary,"client_consequence":consequence,"recommendation":recommendation,"effort":effort,"dependency":dependency,"auditor_notes":notes,"report_override":override}); st.success(L("Assessment saved.")); st.rerun()
        refreshed=db.get_audit_problem(audit["id"],selected_id); score_cols=st.columns(4); score_cols[0].metric(L("Weighted score"),refreshed["weighted_score"]); score_cols[1].metric(L("Priority tier"),refreshed["priority_tier"].split(" — ")[0]); score_cols[2].metric(L("Include in report"),L("Yes") if refreshed["include_in_report"] else L("No")); score_cols[3].metric(L("Roadmap"),refreshed["roadmap_phase"].split(" — ")[0])
        st.subheader(L("Attachments")); uploads=st.file_uploader(L("Attach evidence files"),accept_multiple_files=True,type=["pdf","xlsx","xls","csv","docx","txt","png","jpg","jpeg","webp","json"],key=f"files_{selected_id}")
        if uploads and st.button(L("Save uploaded files"),key=f"save_files_{selected_id}"):
            for upload in uploads: db.save_attachment(audit["id"],selected_id,upload)
            st.success(L("Saved {count} file(s).",count=len(uploads))); st.rerun()
        for attachment in db.list_attachments(audit["id"],selected_id):
            c1,c2,c3=st.columns([5,1,1]); c1.write(f"📎 {attachment['original_name']} · {round(attachment['size_bytes']/1024,1)} KB"); payload=db.get_attachment_bytes(attachment["id"])
            if payload: c2.download_button(L("Download"),data=payload[1],file_name=payload[0],key=f"dl_{attachment['id']}")
            if c3.button(L("Delete"),key=f"del_att_{attachment['id']}"): db.delete_attachment(attachment["id"]); st.rerun()


def render_findings_page() -> None:
    audit=require_audit(); page_header("Step 3","Findings & Roadmap","Select the few findings that explain the result, protect strengths and build an action sequence.")
    candidates=db.get_report_candidates(audit["id"]); current_findings=db.get_findings(audit["id"]); current_ids=[f["problem_id"] for f in current_findings]; auto_ids=[c["problem_id"] for c in sorted(candidates,key=lambda x:(-x["weighted_score"],x["display_order"])) if c["include_in_report"]][:10]
    tab1,tab2,tab3=st.tabs([L("Key findings"),L("Protected strengths"),L("Roadmap")])
    with tab1:
        if not candidates: st.info(L("Confirm or suspect problems in Diagnosis first."))
        else:
            labels={c["problem_id"]:f"{c['problem_id']} · {localize_problem(c,lang())['problem']} · {V(c['priority_tier'])} · {L('Score {score}',score=c['weighted_score'])}" for c in candidates}
            selected=st.multiselect(L("Findings for the client report (recommended: 3–10)"),[c["problem_id"] for c in candidates],default=current_ids or auto_ids,format_func=lambda x:labels[x])
            c1,c2=st.columns([1,4])
            if c1.button(L("Save selection"),type="primary",use_container_width=True): db.save_findings(audit["id"],selected); st.success(L("Findings saved.")); st.rerun()
            if c2.button(L("Use automatic suggestions")): db.save_findings(audit["id"],auto_ids); st.rerun()
        for raw in db.get_findings(audit["id"]):
            finding=localize_problem(raw,lang())
            with st.expander(f"#{finding['rank']} · {finding['problem']} · {V(finding['priority_tier'])}",expanded=finding["rank"]==1):
                st.caption(L("Evidence: {evidence} · Confidence: {confidence}% · Score: {score}",evidence=V(finding['evidence_strength']),confidence=finding['confidence'],score=finding['weighted_score'])); st.write(finding["evidence_summary"] or L("Evidence summary is empty.")); c1,c2,c3,c4=st.columns(4)
                rank=c1.number_input(L("Rank"),min_value=1,max_value=20,value=int(finding["rank"]),key=f"fr_{finding['problem_id']}"); owner=c2.text_input(L("Owner"),value=finding["owner"],key=f"fo_{finding['problem_id']}"); target_date=c3.text_input(L("Target date"),value=finding["target_date"],key=f"ft_{finding['problem_id']}"); status=c4.selectbox(L("Status"),EXECUTION_STATUS,index=EXECUTION_STATUS.index(finding["finding_status"]),key=f"fs_{finding['problem_id']}",format_func=lambda x:V(x))
                if st.button(L("Save finding details"),key=f"save_f_{finding['problem_id']}"): db.update_finding(audit["id"],finding["problem_id"],int(rank),owner,target_date,status); st.rerun()
    with tab2:
        st.caption(L("Only include strengths supported by evidence. This section prevents useful systems from being damaged during change."))
        with st.form("new_strength"):
            title=st.text_input(L("Strength")); evidence=st.text_area(L("Evidence")); preserve=st.text_area(L("What must be preserved"))
            if st.form_submit_button(L("Add protected strength"),type="primary") and title.strip(): db.add_strength(audit["id"],title.strip(),evidence,preserve); st.rerun()
        for strength in db.list_strengths(audit["id"]):
            with st.container(border=True):
                c1,c2=st.columns([8,1]); c1.markdown(f"### {strength['title']}"); c1.write(strength["evidence"]); c1.caption(L("Protect: {text}",text=strength['preserve_guidance']))
                if c2.button(L("Delete"),key=f"ds_{strength['id']}"): db.delete_strength(strength["id"]); st.rerun()
    with tab3:
        finding_options=[f["problem_id"] for f in db.get_findings(audit["id"])]
        with st.form("new_action"):
            st.subheader(L("Add action")); c1,c2=st.columns([1.2,2]); phase=c1.selectbox(L("Phase"),PHASE_OPTIONS,format_func=lambda x:V(x)); action=c2.text_input(L("Action / solution direction")); related=st.multiselect(L("Related findings"),finding_options); c3,c4,c5=st.columns(3); expected=c3.text_area(L("Expected impact")); metric=c4.text_input(L("Success metric")); owner=c5.text_input(L("Owner")); c6,c7,c8,c9=st.columns(4); baseline=c6.text_input(L("Baseline")); target=c7.text_input(L("Target")); effort=c8.selectbox(L("Effort"),EFFORT_OPTIONS); target_date=c9.text_input(L("Target date")); dependency=st.text_input(L("Dependency")); notes=st.text_area(L("Notes / scope"))
            if st.form_submit_button(L("Add roadmap action"),type="primary"):
                if not action.strip(): st.error(L("Action is required."))
                else: db.add_roadmap_action(audit["id"],{"phase":phase,"action":action,"related_problem_ids":"; ".join(related),"expected_impact":expected,"success_metric":metric,"baseline":baseline,"target":target,"owner":owner,"effort":effort,"dependency":dependency,"target_date":target_date,"status":"Not Started","notes":notes}); st.rerun()
        for item in db.list_roadmap_actions(audit["id"]):
            with st.expander(f"{V(item['phase'])} · {item['action']}"):
                st.write(item["expected_impact"]); st.caption(L("Metric: {metric} · {baseline} → {target} · Owner: {owner} · Effort: {effort}",metric=item['success_metric'],baseline=item['baseline'],target=item['target'],owner=item['owner'],effort=item['effort']))
                if st.button(L("Delete action"),key=f"da_{item['id']}"): db.delete_roadmap_action(item["id"]); st.rerun()


def render_report_page() -> None:
    audit=require_audit(); page_header("Step 4","Report","Visual executive report plus the full technical audit register."); summary=db.dashboard_summary(audit["id"])
    if summary["primary_count"]!=1: st.warning(L("Select exactly one Primary Constraint before finalizing the report."))
    if summary["confirmed"] and summary["evidence_coverage"]<100: st.warning(L("Some confirmed findings have no evidence strength."))
    html_report=build_report_html(audit["id"]); pdf_report=build_report_pdf(audit["id"]); register_csv=build_audit_register_csv(audit["id"])
    c1,c2,c3=st.columns([1.25,1.35,3.2])
    safe_name="".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in audit['client_name']).strip("_") or "Client"
    c1.download_button(L("Download PDF report"),data=pdf_report,file_name=f"VELAR_{safe_name}_Report.pdf",mime="application/pdf",use_container_width=True)
    c2.download_button(L("Download audit register CSV"),data=register_csv,file_name=f"VELAR_{safe_name}_Audit_Register.csv",mime="text/csv",use_container_width=True)
    
    st.caption(L("Report preview"))
    components.html(html_report,height=1150,scrolling=True)


render_sidebar()
page=st.session_state.page
if page=="Audits": render_audits_page()
elif page=="Overview": render_overview_page()
elif page=="Profile": render_profile_page()
elif page=="Diagnosis": render_diagnosis_page()
elif page=="Findings": render_findings_page()
elif page=="Report": render_report_page()
else: st.session_state.page="Audits"; st.rerun()

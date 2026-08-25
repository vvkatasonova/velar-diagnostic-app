# Velar Diagnostic App

**Prototype v0.4 · internal business-audit workspace**

Velar Diagnostic App turns the Velar Diagnostic Playbook into a working audit workflow:

**Client Profile → Diagnosis → Primary Constraint → Findings → Roadmap → Client Report**

This repository contains a working prototype, not a finished commercial product. The goal of the current version is to validate the audit logic, data model, prioritization workflow and report generation before a future UI/product redesign.

## What the application does

- creates and stores separate business audits;
- captures client context, baseline metrics, data availability and audit scope;
- loads a library of **175 diagnostic hypotheses** across Marketing, Sales, Operations, Finance and Profit Output;
- lets an auditor review each problem, document evidence, attach files and assign a causal role;
- calculates a rule-based Weighted Score and Priority Tier;
- enforces a single Primary Constraint per audit;
- lets the auditor select the small set of findings that should appear in the client report;
- records strengths that should not be broken during implementation;
- builds a phased action roadmap;
- generates an English PDF client report and a complete CSV audit register.

## Interface languages

The internal interface supports:

- English
- Ukrainian

Use the two flag buttons in the top-right corner of every page to switch the interface.

The **client report is always generated in English**, regardless of the current interface language.

## Important product boundaries

This version deliberately does **not** pretend to automate expert judgement.

- Attachments are stored and linked to a Problem ID, but they are not automatically read or analysed.
- The auditor decides whether an issue is Confirmed, Suspected, Not Present or Not Applicable.
- The auditor assigns the Causal Role.
- The auditor selects the single Primary Constraint.
- The score supports prioritization; it does not prove causality by itself.

The core methodology is therefore:

**Evidence → Causal Analysis → Priority → Action**

## Prioritization logic

The base impact score uses four client-specific factors:

```text
(Revenue Impact × 35 + Flow Restriction × 30 + Urgency × 20 + Scale Risk × 15) ÷ 5
```

Bonuses:

- `+12` if the problem is selected as the Primary Constraint;
- `+8` for Red base criticality;
- `+4` for Yellow base criticality.

Then the score is multiplied by:

- Status multiplier;
- Evidence Strength multiplier;
- auditor Confidence.

The final score is capped at `100`.

Priority Tiers:

```text
P1 — Primary Constraint
P2 — Critical Revenue Leak
P3 — Bottleneck / Stability
P4 — Optimization / Monitor
```

See [`docs/scoring.md`](docs/scoring.md) for the complete rule set.

## Report output

The application creates the PDF directly with Python. It does **not** rely on browser printing, so the exported report does not contain local file paths, browser dates or browser headers/footers.

The report currently contains:

1. Executive Summary
2. Revenue Flow Map
3. Flow Risk Profile
4. Primary Constraint case
5. Causal Chain
6. Key Findings
7. Protected Strengths
8. Optimization Roadmap
9. Audit Register appendix

The report is intentionally more visual and selective than a raw audit spreadsheet. The full technical register remains available separately as CSV.

## Project structure

```text
velar-diagnostic-app/
├── app.py                  # Streamlit interface
├── db.py                   # SQLite schema, storage and scoring logic
├── i18n.py                 # EN / UA interface localization
├── reporting.py            # HTML preview, PDF report and CSV export
├── sample_case.py          # synthetic development fixture
├── seed_sample.py          # optional sample-data loader
├── data/
│   └── problem_library.json
├── docs/
│   ├── architecture.md
│   ├── scoring.md
│   ├── report_logic.md
│   └── sample_case.md
├── examples/
│   └── sample_report.pdf
├── uploads/
│   └── .gitkeep
├── requirements.txt
├── run_velar.ps1
├── run_velar.bat
└── README.md
```

## Run on Windows

### Fastest way

Double-click `run_velar.bat` in the project folder. It creates `.venv`, installs the dependencies and starts Streamlit without requiring a PowerShell execution-policy change.

If you prefer PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_velar.ps1
```

Then open:

```text
http://localhost:8501
```

### Manual run

```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

SQLite is included with Python, so no paid database service is required for local use.

## Optional synthetic sample

The main UI starts clean and does not contain a “Create demo audit” button.

For development, screenshots or testing, a synthetic Northstar sample can be seeded manually:

```powershell
py seed_sample.py
```

The fixture is stored separately in [`sample_case.py`](sample_case.py). It is not real client data and it is not generated by AI at runtime.

A PDF produced from that fixture is included at [`examples/sample_report.pdf`](examples/sample_report.pdf).

## Storage

Local development uses SQLite:

```text
data/velar.db
```

That file is excluded from Git. Attachments are stored under `uploads/` and are also excluded from Git.

For a future hosted multi-user version, persistent cloud storage and authentication would replace local SQLite/filesystem storage.

## Current limitations / next iteration

The next product iteration should focus on simplification rather than adding more features:

- reduce the number of fields visible by default;
- move advanced scoring fields behind expandable sections;
- improve navigation through the 175-problem library;
- add structured Evidence Log records instead of only file attachments and summaries;
- optionally parse supported data exports;
- add stronger report editing/customization;
- move from the prototype Streamlit UI to a dedicated frontend after workflow validation.

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — application structure and data flow
- [`docs/scoring.md`](docs/scoring.md) — scoring and priority logic
- [`docs/report_logic.md`](docs/report_logic.md) — where each report section gets its data
- [`docs/sample_case.md`](docs/sample_case.md) — synthetic sample and why it exists

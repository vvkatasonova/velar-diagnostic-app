# VELAR Methodology and Venture Background

> **VELAR is the working title of an independently developed business-diagnostic system and early-stage venture concept.**

## At a glance

- **Purpose:** turn fragmented business information into evidence-bounded findings, one primary constraint, and a sequenced improvement roadmap.
- **Current form:** an internal diagnostic playbook and a functional local web application.
- **Methodology base:** 175 diagnostic hypotheses across five connected business flows.
- **Current validation:** one anonymous pilot with an operating small business.
- **Venture status:** pre-commercial and not yet a registered or operating consulting company.

## Why VELAR was developed

Small businesses rarely have only one visible problem. They may face unstable demand, lost inquiries, overloaded delivery, weak financial visibility, or inconsistent profit at the same time. Treating every symptom as equally urgent creates long lists of recommendations without a clear starting point.

VELAR was developed to support a more disciplined question:

**Which verified issue currently restricts the overall business flow the most, and what should be changed first?**

The system is deliberately designed as decision support for an auditor. It does not claim to analyse a company automatically, interpret every uploaded document, or prove causality through a score alone.

## Revenue-flow model

VELAR models a business as a connected flow rather than a set of isolated departments.

```mermaid
flowchart LR
    M[Marketing] --> S[Sales] --> O[Operations] --> F[Finance] --> P[Profit Output]
```

| Flow | Diagnostic question |
|---|---|
| Marketing | Does enough relevant and sufficiently stable demand enter the business? |
| Sales | Does incoming demand convert into paying customers? |
| Operations | Can the business deliver its promise consistently and at the required capacity? |
| Finance | Does revenue become a sustainable economic and cash position? |
| Profit Output | Does the full system produce repeatable, profitable, and scalable results? |

Weakness in one flow can affect every later stage. More leads, for example, do not solve a sales process that loses inquiries or an operation that cannot handle additional demand.

## Problem classification

The diagnostic library classifies each hypothesis by its primary effect on the business system.

| Type | Meaning |
|---|---|
| Revenue Leak | Direct loss of leads, conversion, revenue, cash, or margin. |
| Bottleneck | A restriction on speed, throughput, capacity, or growth. |
| Operational Turbulence | Instability, inconsistency, errors, or unclear execution. |
| Scale Risk | A weakness likely to intensify or break the system as demand grows. |

These types describe how a problem affects the flow. They do not determine whether the problem exists for a particular client. That decision requires client-specific evidence.

## Diagnostic workflow

The current workflow combines the methodology, spreadsheet playbook, and web application.

1. **Define the business context and audit scope.** Record the business model, offer, target customer, baseline metrics, available data, exclusions, and access limitations.
2. **Collect evidence safely.** Use interviews, analytics, exports, financial reports, observations, or screenshots. Prefer read-only access and never request passwords.
3. **Review relevant hypotheses.** Work through the diagnostic library by flow and group instead of beginning with an assumed solution.
4. **Record a status.** Mark each reviewed hypothesis as Not Present, Suspected, Confirmed, or Not Applicable. Unreviewed items remain Not Checked.
5. **Assess evidence and impact.** Record evidence strength, revenue impact, flow restriction, urgency, scale risk, and auditor confidence.
6. **Build the causal picture.** Distinguish root causes, contributing causes, symptoms, and standalone issues. The system allows uncertainty rather than forcing every finding into a root-cause claim.
7. **Select one Primary Constraint.** The auditor chooses the verified issue that most restricts the overall flow within the defined scope.
8. **Create the client output.** Select key findings, preserve existing strengths, and convert recommendations into sequenced actions with owners, dependencies, metrics, and target dates.

## Evidence rules

Evidence is treated as the boundary of every conclusion.

- A hypothesis in the library is not a finding by itself.
- A Confirmed finding requires a clear evidence summary.
- Evidence strength describes the quality of support, not the size of the problem.
- Scope and access limitations must appear in the final report.
- A lack of data must not be reported as proof that a flow is healthy.
- Interview-only conclusions must be identified as such and expressed with appropriate confidence.
- Attachments can be stored and linked to a Problem ID, but the current application does not interpret their contents automatically.

## Prioritization logic

The base impact score combines four client-specific factors:

```text
(Revenue Impact × 35 + Flow Restriction × 30 + Urgency × 20 + Scale Risk × 15) ÷ 5
```

The application then applies status, evidence-strength, and auditor-confidence multipliers, together with limited bonuses for base criticality and Primary Constraint selection. The final score is capped at 100.

Priority tiers are:

- **P1 — Primary Constraint**
- **P2 — Critical Revenue Leak**
- **P3 — Bottleneck / Stability**
- **P4 — Optimization / Monitor**

The score supports consistent prioritization. It does not replace causal analysis or the auditor's documented judgement.

## System components

VELAR developed through several connected artifacts rather than beginning as a standalone application.

### Diagnostic playbook

The spreadsheet playbook contains:

- a Client Profile and audit context;
- a library of 175 unique diagnostic hypotheses;
- a client-specific Audit Workspace;
- a structured Evidence Log;
- Key Findings and Roadmap worksheets;
- a diagnostic Dashboard;
- controlled values and definitions.

### Auditor manual

A 33-page internal manual documents how to prepare an audit, interpret every field, evaluate evidence, apply scoring, choose the Primary Constraint, build findings and actions, and perform quality checks. It was written as an internal operating manual and is not presented as external validation of the methodology.

### Web application

The local Streamlit application transfers the same workflow into a structured interface with SQLite storage, bilingual internal navigation, problem filtering, scoring, Primary Constraint enforcement, findings, protected strengths, roadmap management, PDF generation, and CSV export.

### Pilot evidence

The application was used for an anonymous limited diagnostic of an operating independent tattoo studio in Ukraine. Twelve relevant hypotheses were reviewed, four findings were confirmed with moderate interview-based evidence, and one Primary Constraint was selected among the reviewed hypotheses. The system generated a ten-page report and phased roadmap.

After reviewing the report, the owner confirmed that the prioritization corresponded to the real situation and considered the recommendations logical, realistic, and suitable for gradual implementation. This validates the usability of the workflow and the relevance of the output for one case. It does not yet demonstrate measured business impact.

## Venture concept

VELAR is intended to become the internal diagnostic system of a future consulting practice, not a self-service public SaaS product.

The proposed venture path is:

1. **Diagnostic audit:** identify verified constraints, leaks, risks, and protected strengths.
2. **Targeted implementation:** help the client implement selected process, measurement, or automation improvements where appropriate.
3. **Ongoing optimization:** monitor agreed metrics and refine the operating system over time.

This commercial model remains a hypothesis. No claim is made that VELAR is already an established company, has recurring revenue, or has validated pricing.

The planned initial niche is B2B online service businesses with approximately 5–50 employees, including marketing, software, recruitment, and consulting agencies. These businesses typically sell through calls or messaging and deliver through a team. The tattoo-studio pilot tested the diagnostic workflow on a smaller B2C service business; it did not validate the intended niche or the commercial model.

## Development evolution

Early concept documents explored a narrower automation-led service, rapid audit promises, ROI estimates, and a four-part framework. Further work exposed the limits of those assumptions. The current system therefore:

- uses five connected business flows rather than treating automation as a separate diagnostic objective;
- evaluates 175 structured hypotheses instead of a short generic checklist;
- requires evidence and explicit scope limitations;
- separates causal role from numerical priority;
- protects processes that already work;
- avoids unsupported ROI claims;
- recommends simple operational fixes when they are more appropriate than software or AI.

This evolution is important to the project: VELAR is the result of repeated methodological revision, not only interface development.

## Current limitations and next validation stage

- The methodology has been tested on only one real business.
- The pilot relied primarily on an owner interview rather than independent access to operational and financial systems.
- The proposed actions have not yet been monitored long enough to measure financial or operational impact.
- The initial target niche has not yet been validated through multiple pilots.
- Scoring thresholds require further calibration across different industries and business sizes.
- The application currently runs locally and does not include authentication or multi-user infrastructure.

The next stage is to conduct additional evidence-based pilots, compare scoring and recommendations across cases, monitor implementation outcomes, and refine the methodology before expanding the product or commercial offer.

---

**Developed by Veronika Katasonova · 2026**

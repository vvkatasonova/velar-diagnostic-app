# Report Data Lineage

The client-facing PDF is generated directly by Python/ReportLab. Browser printing is not used, so local file paths and browser headers are not part of the report.

The report generator does not invent audit results. Each block has a defined source.

| Report block | Source in the application |
|---|---|
| Cover | Audit header + Client Profile |
| Executive Summary | `executive_summary` from Client Profile, or a simple fallback summary |
| Baseline metric cards | `baseline_metrics` |
| Revenue Flow Map | `dashboard_summary()` calculated from reviewed problem statuses and scores |
| Flow risk bars | maximum Weighted Score in each flow |
| Primary Constraint | the single problem explicitly marked `primary_constraint = Yes` |
| Why we are confident | Status, Evidence Strength, Confidence, Weighted Score and Causal Role |
| Causal Chain | selected findings grouped by auditor-assigned Causal Role |
| Key Findings | saved Findings selection; falls back to rule-based included candidates if none saved |
| Protected Strengths | manually entered strengths |
| Optimization Roadmap | manually entered roadmap actions |
| Audit Register | every reviewed problem (`Status != Not Checked`) |

## Important boundary

Attachments are stored under `uploads/<audit_id>/<problem_id>/` and linked to the relevant problem. The current prototype **does not parse, summarize or score the content of uploaded files automatically**. The auditor reads the source and records the Evidence Summary / assessment manually.

## Automatic suggestions

Automatic finding suggestions are not AI. Candidates are sorted by rule-based `Weighted Score`, and only issues marked for report inclusion by the rules are suggested. The auditor can accept, change or replace the selection.

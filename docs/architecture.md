# Architecture

```text
Streamlit UI
    ↓
SQLite data layer
    ├── Audit + Client Profile
    ├── Baseline Metrics
    ├── 175-problem read-only methodology library
    ├── Client-specific assessments
    ├── Attachments linked to Problem IDs
    ├── Findings + Protected Strengths
    └── Roadmap Actions
    ↓
Rule-based scoring / prioritization
    ↓
Report generator
    ├── Executive Summary
    ├── Revenue Flow Map + risk profile
    ├── Primary Constraint case
    ├── Causal Chain
    ├── Key Findings
    ├── Protected Strengths
    ├── Optimization Roadmap
    └── Audit Register
```

The library represents reusable diagnostic hypotheses. Every audit creates a separate client-specific assessment row for every active Problem ID.

The prototype intentionally keeps the architecture local and inspectable: Streamlit + SQLite + Python report generation. No paid services are required to run it.

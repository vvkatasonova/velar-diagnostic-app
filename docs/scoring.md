# Scoring logic

The score is a decision-support mechanism, not an automatic diagnosis.

Base impact:

```text
(Revenue Impact × 35 + Flow Restriction × 30 + Urgency × 20 + Scale Risk × 15) ÷ 5
```

Bonuses are additive:

- +12 for Primary Constraint;
- +8 for Red base criticality;
- +4 for Yellow base criticality;
- +0 for Green.

Multipliers:

- Status: Confirmed 1.0; Suspected 0.65; other statuses 0;
- Evidence: Strong 1.0; Moderate 0.8; Weak 0.6; None 0.4;
- Confidence: 0%, 25%, 50%, 75%, 100%.

```text
Weighted Score = min(100, round((Base impact + bonuses) × Status × Evidence × Confidence))
```

Priority Tier:

- P1 — explicitly selected Primary Constraint;
- P2 — Revenue Leak with score ≥ 65;
- P3 — score ≥ 45 when not P1/P2;
- P4 — remaining non-zero scores.

The score supports ranking. Causal Role and the Primary Constraint remain auditor decisions.

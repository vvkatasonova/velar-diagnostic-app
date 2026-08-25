from __future__ import annotations

"""Synthetic sample case used only to demonstrate the prototype.

The values are intentionally stored outside the production database logic so the
sample can be replaced or removed without changing the application itself.
No client data is contained in this file.
"""

SAMPLE_AUDIT = {
    "client_name": "Northstar Home Services (Sample)",
    "audit_name": "Sample Revenue Flow Audit",
    "industry": "Home Services",
}

SAMPLE_PROFILE = {
    "website": "https://example.com",
    "market_geography": "United States",
    "auditor": "Velar Prototype",
    "business_model": "One-time services + recurring service plans",
    "main_offer": "HVAC, plumbing and electrical services",
    "target_customer": "Homeowners in local service areas",
    "lead_sources": "Google Ads 60%, referrals 30%, organic 10%",
    "sales_motion": "Call/form → dispatcher → estimate → booking → service",
    "delivery_model": "Local technician teams",
    "team_size": "24",
    "self_reported_constraint": "We need more leads",
    "growth_goal": "Increase monthly revenue from $180k to $240k without sharply increasing ad spend",
    "marketing_data": "Yes",
    "sales_data": "Partial",
    "operations_data": "Yes",
    "financial_data": "Partial",
    "access_limitations": "CRM data is a partial sample; financial values are management estimates.",
    "audit_scope": "Marketing, Sales, Operations, Finance and Profit Output. Tax, legal and cybersecurity are excluded.",
    "executive_summary": (
        "Demand is sufficient for the current growth goal, but Sales Flow loses paid demand before contact and booking. "
        "The strongest evidence points to delayed first response and uncontrolled inbound handling as the current primary constraint."
    ),
}

SAMPLE_METRICS = {
    "Leads": ("300", "per month", "Google Ads + call tracking, 6-month range"),
    "Lead → Customer Conversion": ("18", "%", "CRM sample"),
    "Average Response Time": ("2h25m", "median", "Call tracking export"),
    "Revenue": ("180000", "USD/month", "Management estimate"),
    "Team Capacity": ("25", "% additional capacity", "Operations capacity report"),
}

# Problem IDs match the current v2 problem library.
SAMPLE_PROBLEMS = {
    # Slow response to inquiries
    "S-B01": {
        "status": "Confirmed", "evidence_strength": "Strong",
        "revenue_impact": 5, "flow_restriction": 5, "urgency": 5, "scale_risk": 3,
        "confidence": 100, "primary_constraint": 1, "causal_role": "Root Cause",
        "evidence_summary": "31% of inbound calls were not answered live; 19% had no callback within 24 hours. Median first response: 2h25m.",
        "client_consequence": "Paid demand is lost before contact, increasing effective acquisition cost and reducing bookings.",
        "recommendation": "Create a shared inbound queue, ownership by shift and a 15-minute response SLA.",
        "effort": "M", "report_override": "Auto",
    },
    # Inbound inquiries are lost
    "S-A01": {
        "status": "Confirmed", "evidence_strength": "Strong",
        "revenue_impact": 5, "flow_restriction": 4, "urgency": 5, "scale_risk": 3,
        "confidence": 100, "primary_constraint": 0, "causal_role": "Contributing Cause",
        "evidence_summary": "Call tracking showed that 31% of calls were not answered live and a material share never received a timely callback.",
        "client_consequence": "High-intent prospects can leave the funnel before a sales conversation happens.",
        "recommendation": "Add backup ownership, missed-inquiry alerts and daily control of uncontacted leads.",
        "effort": "S", "report_override": "Auto",
    },
    # No clear follow-up sequence
    "S-C03": {
        "status": "Confirmed", "evidence_strength": "Moderate",
        "revenue_impact": 4, "flow_restriction": 4, "urgency": 4, "scale_risk": 4,
        "confidence": 75, "primary_constraint": 0, "causal_role": "Contributing Cause",
        "evidence_summary": "19% of sampled leads had no recorded next action or callback within 24 hours; follow-up depended on individual memory.",
        "client_consequence": "Leads continue leaking after the first contact attempt and pipeline outcomes become inconsistent.",
        "recommendation": "Implement a mandatory follow-up sequence and next-action control in the lead workflow.",
        "effort": "M", "report_override": "Auto",
    },
    # Low lead-to-customer conversion
    "S-D05": {
        "status": "Confirmed", "evidence_strength": "Strong",
        "revenue_impact": 5, "flow_restriction": 4, "urgency": 4, "scale_risk": 3,
        "confidence": 100, "primary_constraint": 0, "causal_role": "Symptom",
        "evidence_summary": "Conversion was 29% when contacted within 15 minutes versus 9% after two hours in the reviewed sample.",
        "client_consequence": "Low conversion is a measurable downstream symptom of response and follow-up failures.",
        "recommendation": "Track conversion by response-time band and validate the change after response controls are introduced.",
        "effort": "S", "report_override": "Auto",
    },
    # Team cannot handle the current workload — explicitly disproved in sample
    "O-B02": {
        "status": "Not Present", "evidence_strength": "Strong",
        "revenue_impact": 2, "flow_restriction": 2, "urgency": 2, "scale_risk": 3,
        "confidence": 100, "primary_constraint": 0, "causal_role": "Standalone",
        "evidence_summary": "Capacity report indicates current delivery teams can support approximately 25% more booked jobs.",
        "client_consequence": "Operations capacity is not the current constraint.",
        "recommendation": "Preserve service quality while increasing booked volume.",
        "effort": "S", "report_override": "Auto",
    },
}

SAMPLE_FINDINGS = ["S-B01", "S-A01", "S-C03", "S-D05"]

SAMPLE_STRENGTHS = [
    (
        "Stable lead volume",
        "Lead volume stayed between approximately 280–330 per month for six months and acquisition cost remained within target.",
        "Do not increase acquisition spend before fixing response and follow-up."
    ),
    (
        "Available delivery capacity",
        "Technician capacity data indicates the delivery system can support approximately 25% more booked jobs.",
        "Protect service quality while booked volume increases."
    ),
]

SAMPLE_ROADMAP = [
    {
        "phase": "Phase 1 — Fix Primary Constraint",
        "action": "Create shared inbound queue and ownership by shift",
        "related_problem_ids": "S-B01; S-A01",
        "expected_impact": "Lower inquiry loss and faster contact",
        "success_metric": "Unanswered lead share",
        "baseline": "31%", "target": "<5% in 30 days",
        "owner": "Sales Manager", "effort": "M", "dependency": "Approved shifts",
        "status": "Not Started",
    },
    {
        "phase": "Phase 1 — Fix Primary Constraint",
        "action": "Introduce 15-minute first-response SLA and real-time alerts",
        "related_problem_ids": "S-B01",
        "expected_impact": "Higher contact and booking rate",
        "success_metric": "Median first response",
        "baseline": "2h25m", "target": "≤15m",
        "owner": "Sales Manager", "effort": "S", "dependency": "Shared inbound queue",
        "status": "Not Started",
    },
    {
        "phase": "Phase 2 — Stop Critical Leaks",
        "action": "Implement mandatory follow-up sequence and next-action control",
        "related_problem_ids": "S-C03",
        "expected_impact": "Fewer leads lost after the first contact attempt",
        "success_metric": "Leads without next action",
        "baseline": "19%", "target": "<3%",
        "owner": "Sales Ops", "effort": "M", "dependency": "CRM stages confirmed",
        "status": "Not Started",
    },
    {
        "phase": "Phase 3 — Stabilize Operations",
        "action": "Review a weekly QA sample and coach dispatchers on response standards",
        "related_problem_ids": "S-B01; S-C03",
        "expected_impact": "More consistent execution after the workflow change",
        "success_metric": "Contact-to-booking conversion",
        "baseline": "18%", "target": "Target set after 4-week controlled baseline",
        "owner": "Sales Manager", "effort": "S", "dependency": "SLA and follow-up active",
        "status": "Not Started",
    },
    {
        "phase": "Phase 4 — Optimize & Scale",
        "action": "Evaluate automation and routing only after the response process is stable",
        "related_problem_ids": "S-B01; S-A01",
        "expected_impact": "Lower manual handling time without automating a broken process",
        "success_metric": "Manual handling time",
        "baseline": "To be measured", "target": "Target after stabilization",
        "owner": "Sales Ops", "effort": "M", "dependency": "30 days of stable process data",
        "status": "Not Started",
    },
]

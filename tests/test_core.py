from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import db
from reporting import build_report_pdf


class VelarCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        db.DATABASE_PATH = root / "velar_test.db"
        db.UPLOADS_DIR = root / "uploads"
        db.init_database()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_problem_library_contains_175_active_hypotheses(self) -> None:
        with db.get_connection() as con:
            count = con.execute("SELECT COUNT(*) FROM problem_library WHERE active='Yes'").fetchone()[0]
        self.assertEqual(count, 175)

    def test_primary_constraint_is_unique_and_scored(self) -> None:
        audit_id = db.create_audit("Test Client", "Test Audit", "B2B Services")
        payload = {
            "status": "Confirmed",
            "evidence_strength": "Strong",
            "revenue_impact": 5,
            "flow_restriction": 5,
            "urgency": 5,
            "scale_risk": 4,
            "confidence": 100,
            "primary_constraint": 1,
            "causal_role": "Root Cause",
        }
        db.save_audit_problem(audit_id, "S-B01", payload)
        first = db.get_audit_problem(audit_id, "S-B01")
        self.assertEqual(first["priority_tier"], "P1 — Primary Constraint")
        self.assertGreater(first["weighted_score"], 0)

        db.save_audit_problem(audit_id, "S-A01", payload)
        self.assertEqual(db.get_primary_constraint(audit_id)["problem_id"], "S-A01")
        self.assertEqual(db.get_audit_problem(audit_id, "S-B01")["primary_constraint"], 0)

    def test_pdf_is_generated_directly(self) -> None:
        audit_id = db.create_sample_audit()
        pdf = build_report_pdf(audit_id)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 10_000)

    def test_partially_checked_flow_is_not_reported_as_stable(self) -> None:
        audit_id = db.create_audit("Scoped Client", "Scoped Audit", "Services")
        db.save_audit_problem(audit_id, "F-D04", {
            "status": "Not Present",
            "evidence_strength": "Moderate",
            "confidence": 75,
        })
        finance = next(x for x in db.dashboard_summary(audit_id)["by_flow"] if x["flow"] == "Finance")
        self.assertEqual(finance["status"], "Limited Assessment")


if __name__ == "__main__":
    unittest.main()

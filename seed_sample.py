"""Optional development helper: create the synthetic Northstar sample audit.

This is intentionally not exposed as a button in the main UI.
Run it only when you want a prefilled example for screenshots or testing.
"""

import db


def main() -> None:
    db.init_database()
    audit_id = db.create_sample_audit()
    print(f"Sample audit ready. Audit ID: {audit_id}")


if __name__ == "__main__":
    main()

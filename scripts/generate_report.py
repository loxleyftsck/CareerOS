"""
generate_report.py — CLI entry point for CareerOS Automated Reporting.

Usage:
    python scripts/generate_report.py            # Daily report
    python scripts/generate_report.py --weekly   # Weekly summary
    python scripts/generate_report.py --stdout   # Print only, no file save
"""

import os
import sys
import argparse
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from storage import db
from engine.reporting.reports import generate_system_report

def main():
    parser = argparse.ArgumentParser(description="CareerOS Automated Report Generator")
    parser.add_argument("--weekly", action="store_true", help="Generate a weekly summary instead of daily")
    parser.add_argument("--stdout", action="store_true", help="Print report to stdout only (skip saving to file)")
    args = parser.parse_args()

    # Ensure DB is initialized
    db.init_db()

    period = "Weekly" if args.weekly else "Daily"
    report = generate_system_report(period=period)

    print(report)

    if not args.stdout:
        # Save to reports/ directory
        reports_dir = os.path.join(ROOT_DIR, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"careeros_{period.lower()}_report_{timestamp}.md"
        filepath = os.path.join(reports_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n✅ Report saved to: reports/{filename}")

if __name__ == "__main__":
    main()

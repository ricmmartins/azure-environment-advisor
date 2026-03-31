#!/usr/bin/env python3
"""
Azure Environment Advisor — Drift Detection (Assessment Comparison)

Compares two assessment baselines (JSON) and reports:
- New findings (appeared since last assessment)
- Resolved findings (fixed since last assessment)
- Changed severity (escalated or de-escalated)
- Unchanged findings (still present)

Usage:
    python scripts/compare-assessments.py --baseline baselines/baseline-2026-01-01.json --current baselines/baseline-2026-02-01.json
    python scripts/compare-assessments.py --baseline baselines/baseline-2026-01-01.json --current baselines/baseline-2026-02-01.json --output json

Baseline Format:
    The baseline JSON file should follow this schema:

    {
      "metadata": {
        "subscription_id": "abc-12345",
        "subscription_name": "contoso-prod",
        "profile": "startup",
        "date": "2026-01-15",
        "total_resources": 42
      },
      "findings": [
        {
          "rule_id": "SEC-001",
          "title": "Public database endpoints",
          "severity": "Critical",
          "pillar": "Security",
          "resources": ["sql-contoso-prod"],
          "status": "finding"
        }
      ],
      "passed": ["SEC-002", "SEC-003", "REL-001"]
    }

    You can generate this baseline by asking the Copilot agent:
    "Save the assessment results as a JSON baseline to baselines/<date>.json"

Exit codes:
    0 = comparison completed, no regressions
    1 = regressions detected (new Critical/High findings or escalations)
        Only returned when --fail-on-regression is passed
    2 = error occurred
"""

import os
import sys
import json
import argparse
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


# --- Data Classes ---

@dataclass
class FindingDiff:
    rule_id: str
    title: str
    pillar: str
    change_type: str  # "new", "resolved", "escalated", "de-escalated", "unchanged"
    old_severity: str = ""
    new_severity: str = ""
    resources: list = field(default_factory=list)


@dataclass
class ComparisonResult:
    baseline_date: str
    current_date: str
    subscription: str
    new_findings: list[FindingDiff] = field(default_factory=list)
    resolved_findings: list[FindingDiff] = field(default_factory=list)
    escalated: list[FindingDiff] = field(default_factory=list)
    de_escalated: list[FindingDiff] = field(default_factory=list)
    unchanged: list[FindingDiff] = field(default_factory=list)

    @property
    def has_regressions(self) -> bool:
        """True if there are new Critical or High findings, or escalations to Critical/High."""
        for f in self.new_findings:
            if f.new_severity in ("Critical", "High"):
                return True
        for f in self.escalated:
            if f.new_severity in ("Critical", "High"):
                return True
        return False


# --- Comparison Logic ---

SEVERITY_ORDER = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "Informational": 0}


def load_baseline(path: str) -> dict:
    """Load and validate a baseline JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    required_keys = ["metadata", "findings"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Baseline file missing required key: '{key}'")

    return data


def compare_baselines(baseline: dict, current: dict) -> ComparisonResult:
    """Compare two assessment baselines and produce a diff."""
    result = ComparisonResult(
        baseline_date=baseline["metadata"].get("date", "unknown"),
        current_date=current["metadata"].get("date", "unknown"),
        subscription=current["metadata"].get("subscription_name", "unknown"),
    )

    # Index findings by rule_id, excluding accepted exceptions
    old_findings = {f["rule_id"]: f for f in baseline.get("findings", []) if f.get("status", "finding") != "exception"}
    new_findings = {f["rule_id"]: f for f in current.get("findings", []) if f.get("status", "finding") != "exception"}

    all_rule_ids = set(old_findings.keys()) | set(new_findings.keys())

    for rule_id in sorted(all_rule_ids):
        old = old_findings.get(rule_id)
        new = new_findings.get(rule_id)

        if new and not old:
            # New finding
            result.new_findings.append(FindingDiff(
                rule_id=rule_id,
                title=new.get("title", ""),
                pillar=new.get("pillar", ""),
                change_type="new",
                new_severity=new.get("severity", ""),
                resources=new.get("resources", []),
            ))
        elif old and not new:
            # Resolved finding
            result.resolved_findings.append(FindingDiff(
                rule_id=rule_id,
                title=old.get("title", ""),
                pillar=old.get("pillar", ""),
                change_type="resolved",
                old_severity=old.get("severity", ""),
                resources=old.get("resources", []),
            ))
        elif old and new:
            old_sev = old.get("severity", "")
            new_sev = new.get("severity", "")

            if SEVERITY_ORDER.get(new_sev, 0) > SEVERITY_ORDER.get(old_sev, 0):
                result.escalated.append(FindingDiff(
                    rule_id=rule_id,
                    title=new.get("title", ""),
                    pillar=new.get("pillar", ""),
                    change_type="escalated",
                    old_severity=old_sev,
                    new_severity=new_sev,
                    resources=new.get("resources", []),
                ))
            elif SEVERITY_ORDER.get(new_sev, 0) < SEVERITY_ORDER.get(old_sev, 0):
                result.de_escalated.append(FindingDiff(
                    rule_id=rule_id,
                    title=new.get("title", ""),
                    pillar=new.get("pillar", ""),
                    change_type="de-escalated",
                    old_severity=old_sev,
                    new_severity=new_sev,
                    resources=new.get("resources", []),
                ))
            else:
                result.unchanged.append(FindingDiff(
                    rule_id=rule_id,
                    title=new.get("title", ""),
                    pillar=new.get("pillar", ""),
                    change_type="unchanged",
                    old_severity=old_sev,
                    new_severity=new_sev,
                    resources=new.get("resources", []),
                ))

    return result


# --- Output ---

def print_text_report(result: ComparisonResult):
    """Print a human-readable drift detection report."""
    print(f"\n{'='*65}")
    print(f"  Azure Environment Advisor — Drift Detection Report")
    print(f"{'='*65}")
    print(f"  Subscription: {result.subscription}")
    print(f"  Baseline:     {result.baseline_date}")
    print(f"  Current:      {result.current_date}")
    print(f"{'─'*65}")
    print(f"  🆕 New findings:      {len(result.new_findings)}")
    print(f"  ✅ Resolved:          {len(result.resolved_findings)}")
    print(f"  ⬆️  Escalated:         {len(result.escalated)}")
    print(f"  ⬇️  De-escalated:      {len(result.de_escalated)}")
    print(f"  ➡️  Unchanged:         {len(result.unchanged)}")

    if result.new_findings:
        print(f"\n{'─'*65}")
        print("  🆕 NEW FINDINGS")
        print(f"{'─'*65}")
        for f in result.new_findings:
            emoji = "🔴" if f.new_severity == "Critical" else "🟠" if f.new_severity == "High" else "🟡"
            print(f"  {emoji} {f.rule_id} — {f.title} [{f.new_severity}]")
            if f.resources:
                print(f"     Resources: {', '.join(f.resources)}")

    if result.resolved_findings:
        print(f"\n{'─'*65}")
        print("  ✅ RESOLVED FINDINGS")
        print(f"{'─'*65}")
        for f in result.resolved_findings:
            print(f"  ✅ {f.rule_id} — {f.title} [was {f.old_severity}]")

    if result.escalated:
        print(f"\n{'─'*65}")
        print("  ⬆️  ESCALATED (severity increased)")
        print(f"{'─'*65}")
        for f in result.escalated:
            print(f"  ⬆️  {f.rule_id} — {f.title} [{f.old_severity} → {f.new_severity}]")

    if result.de_escalated:
        print(f"\n{'─'*65}")
        print("  ⬇️  DE-ESCALATED (severity decreased)")
        print(f"{'─'*65}")
        for f in result.de_escalated:
            print(f"  ⬇️  {f.rule_id} — {f.title} [{f.old_severity} → {f.new_severity}]")

    print(f"\n{'─'*65}")
    if result.has_regressions:
        print("  🚨 REGRESSIONS DETECTED — New Critical/High findings or escalations")
    else:
        print("  ✅ NO REGRESSIONS — Environment is stable or improving")
    print(f"{'─'*65}\n")


def print_json_report(result: ComparisonResult):
    """Print a JSON drift detection report."""
    report = {
        "subscription": result.subscription,
        "baseline_date": result.baseline_date,
        "current_date": result.current_date,
        "has_regressions": result.has_regressions,
        "summary": {
            "new_findings": len(result.new_findings),
            "resolved": len(result.resolved_findings),
            "escalated": len(result.escalated),
            "de_escalated": len(result.de_escalated),
            "unchanged": len(result.unchanged),
        },
        "new_findings": [{"rule_id": f.rule_id, "title": f.title, "severity": f.new_severity, "pillar": f.pillar, "resources": f.resources} for f in result.new_findings],
        "resolved": [{"rule_id": f.rule_id, "title": f.title, "was_severity": f.old_severity, "pillar": f.pillar} for f in result.resolved_findings],
        "escalated": [{"rule_id": f.rule_id, "title": f.title, "from": f.old_severity, "to": f.new_severity, "pillar": f.pillar} for f in result.escalated],
        "de_escalated": [{"rule_id": f.rule_id, "title": f.title, "from": f.old_severity, "to": f.new_severity, "pillar": f.pillar} for f in result.de_escalated],
    }
    print(json.dumps(report, indent=2))


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Compare two assessment baselines for drift detection")
    parser.add_argument("--baseline", required=True, help="Path to the previous baseline JSON file")
    parser.add_argument("--current", required=True, help="Path to the current baseline JSON file")
    parser.add_argument("--output", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--fail-on-regression", action="store_true",
                        help="Exit with code 1 if regressions are detected (useful in CI)")
    args = parser.parse_args()

    try:
        baseline = load_baseline(args.baseline)
        current = load_baseline(args.current)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"Error loading baseline files: {e}", file=sys.stderr)
        sys.exit(2)

    result = compare_baselines(baseline, current)

    if args.output == "json":
        print_json_report(result)
    else:
        print_text_report(result)

    if args.fail_on_regression and result.has_regressions:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

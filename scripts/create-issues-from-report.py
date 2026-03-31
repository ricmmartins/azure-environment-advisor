#!/usr/bin/env python3
"""
Azure Environment Advisor — Create GitHub Issues from Assessment Report

Parses an assessment HTML report and creates GitHub Issues for Critical and High
severity findings. Each issue includes the rule ID, affected resources,
remediation guidance, and Microsoft Learn documentation links.

Usage:
    python scripts/create-issues-from-report.py --report assessment-report.html
    python scripts/create-issues-from-report.py --report assessment-report.html --severity Critical
    python scripts/create-issues-from-report.py --report assessment-report.html --dry-run
    python scripts/create-issues-from-report.py --report assessment-report.html --labels "auto-finding,sprint-1"

Requirements:
    - Python 3.10+
    - GitHub CLI (gh) installed and authenticated
    - OR set GITHUB_TOKEN environment variable

Exit codes:
    0 = issues created successfully (or dry-run completed)
    1 = error occurred
"""

import os
import re
import sys
import json
import argparse
import subprocess
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path


# --- Data Classes ---

@dataclass
class Finding:
    rule_id: str
    title: str
    severity: str
    pillar: str
    resource: str
    what_found: str
    why_matters: str
    recommendation: str
    learn_more: list[str]


# --- HTML Report Parser ---

class ReportParser(HTMLParser):
    """Parse the assessment HTML report and extract findings."""

    def __init__(self):
        super().__init__()
        self.findings: list[Finding] = []
        self._in_finding = False
        self._current_data = []
        self._current_class = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        css_class = attrs_dict.get("class", "")

        if "finding-card" in css_class or "finding" in css_class:
            self._in_finding = True

        self._current_class = css_class

    def handle_data(self, data):
        if self._in_finding:
            self._current_data.append(data.strip())

    def handle_endtag(self, tag):
        if tag == "div" and self._in_finding:
            self._in_finding = False


def strip_html(text: str) -> str:
    """Remove HTML tags and clean up whitespace."""
    text = re.sub(r'<[^>]+>', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def parse_report_html(html_content: str) -> list[Finding]:
    """
    Parse an assessment HTML report and extract findings.

    Supports three parsing strategies (in order):
    1. Embedded JSON data block (preferred — future-proof)
    2. Structured HTML with data-severity/data-pillar attributes (current report format)
    3. Generic regex fallback
    """
    findings = []

    # Strategy 1: Look for embedded JSON data block
    json_match = re.search(r'<script[^>]*id="findings-data"[^>]*>(.*?)</script>', html_content, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            for item in data:
                findings.append(Finding(**item))
            return findings
        except (json.JSONDecodeError, TypeError):
            pass

    # Strategy 2: Parse structured HTML with data attributes
    # Split findings by their opening div tags, then extract content
    # Matches: <div class="finding..." data-severity="critical" data-pillar="security">
    finding_starts = list(re.finditer(
        r'<div\s+class="finding[^"]*"\s+data-severity="([^"]+)"\s+data-pillar="([^"]+)"[^>]*>',
        html_content
    ))

    for i, start_match in enumerate(finding_starts):
        data_severity = start_match.group(1).strip().capitalize()
        data_pillar = start_match.group(2).strip().capitalize()

        # Extract block content: from this finding start to the next finding start (or end of file)
        block_start = start_match.start()
        block_end = finding_starts[i + 1].start() if i + 1 < len(finding_starts) else len(html_content)
        block = html_content[block_start:block_end]

        # Extract rule ID and title from finding-title
        rule_match = re.search(
            r'class="finding-title"[^>]*>((?:SEC|REL|COST|OPS|PERF|GOV)-\d{3})\s*[—–-]\s*(.+?)</div>',
            block
        )
        if not rule_match:
            continue

        rule_id = rule_match.group(1).strip()
        title = strip_html(rule_match.group(2))

        # Extract resource from finding-resource
        resource = "Subscription-level"
        res_match = re.search(r'class="finding-resource"[^>]*>([^<]+)', block)
        if res_match:
            resource = res_match.group(1).strip()

        # Extract pillar from pillar-tag (more descriptive than data attribute)
        pillar = data_pillar
        pillar_match = re.search(r'class="pillar-tag"[^>]*>[^a-zA-Z]*([^<]+)', block)
        if pillar_match:
            pillar = pillar_match.group(1).strip()

        # Extract body sections (between <h4> headers and the next <h4> or end)
        what_found = ""
        why_matters = ""
        recommendation = ""

        what_match = re.search(r'<h4>What was found</h4>\s*(.*?)(?=<h4>|</div>)', block, re.DOTALL)
        if what_match:
            what_found = strip_html(what_match.group(1))

        why_match = re.search(r'<h4>Why it matters</h4>\s*(.*?)(?=<h4>|</div>)', block, re.DOTALL)
        if why_match:
            why_matters = strip_html(why_match.group(1))

        rec_match = re.search(r'<h4>Recommendation</h4>\s*(.*?)(?=<h4>|</div>)', block, re.DOTALL)
        if rec_match:
            recommendation = strip_html(rec_match.group(1))

        # Extract Learn More links
        learn_more = re.findall(r'href="(https://learn\.microsoft\.com/[^"]+)"', block)

        findings.append(Finding(
            rule_id=rule_id,
            title=title,
            severity=data_severity,
            pillar=pillar,
            resource=resource,
            what_found=what_found,
            why_matters=why_matters,
            recommendation=recommendation,
            learn_more=learn_more,
        ))

    if findings:
        return findings

    # Strategy 3: Generic fallback for unknown HTML formats
    for rule_match in re.finditer(
        r'((?:SEC|REL|COST|OPS|PERF|GOV)-\d{3})\s*[—–-]\s*(.+?)(?:<|$)',
        html_content
    ):
        rule_id = rule_match.group(1)
        title = strip_html(rule_match.group(2))

        severity = "Unknown"
        for sev in ["Critical", "High", "Medium", "Low"]:
            # Look in the surrounding context (200 chars before)
            start = max(0, rule_match.start() - 200)
            context = html_content[start:rule_match.end()]
            if sev.lower() in context.lower():
                severity = sev
                break

        learn_more = re.findall(
            r'href="(https://learn\.microsoft\.com/[^"]+)"',
            html_content[rule_match.start():rule_match.start() + 2000]
        )

        findings.append(Finding(
            rule_id=rule_id,
            title=title,
            severity=severity,
            pillar="Unknown",
            resource="Subscription-level",
            what_found="",
            why_matters="",
            recommendation="",
            learn_more=learn_more,
        ))

    return findings


# --- Issue Creation ---

def format_issue_body(finding: Finding) -> str:
    """Format a finding as a GitHub Issue body."""
    body = f"""## {finding.rule_id} — {finding.title}

| Field | Value |
|-------|-------|
| **Pillar** | {finding.pillar} |
| **Severity** | {finding.severity} |
| **Affected Resource** | `{finding.resource}` |

### What Was Found
{finding.what_found or '_Auto-generated from assessment report. Review the HTML report for full details._'}

### Why It Matters
{finding.why_matters or '_See the assessment report for impact details._'}

### Recommendation
{finding.recommendation or '_See the assessment report for remediation guidance._'}

### Learn More
"""
    if finding.learn_more:
        for link in finding.learn_more:
            body += f"- [{link}]({link})\n"
    else:
        body += "_No documentation links available. Check the rule file for guidance._\n"

    body += f"""
---
_Auto-generated by Azure Environment Advisor assessment._
_Rule: `{finding.rule_id}` | Pillar: {finding.pillar} | Severity: {finding.severity}_
"""
    return body


def create_github_issue(finding: Finding, labels: list[str], dry_run: bool = False) -> bool:
    """Create a GitHub Issue using the GitHub CLI."""
    title = f"[{finding.severity}] {finding.rule_id} — {finding.title}"
    body = format_issue_body(finding)

    all_labels = labels + [
        f"pillar:{finding.pillar.lower().replace(' ', '-')}",
        f"severity:{finding.severity.lower()}",
        "assessment-finding",
    ]
    label_str = ",".join(all_labels)

    if dry_run:
        print(f"  [DRY RUN] Would create issue: {title}")
        print(f"            Labels: {label_str}")
        return True

    try:
        cmd = [
            "gh", "issue", "create",
            "--title", title,
            "--body", body,
            "--label", label_str,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            issue_url = result.stdout.strip()
            print(f"  ✅ Created: {issue_url}")
            return True
        else:
            print(f"  ❌ Failed to create issue for {finding.rule_id}: {result.stderr.strip()}")
            return False

    except FileNotFoundError:
        print("  ❌ GitHub CLI (gh) not found. Install it: https://cli.github.com/")
        return False
    except subprocess.TimeoutExpired:
        print(f"  ❌ Timeout creating issue for {finding.rule_id}")
        return False


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Create GitHub Issues from assessment findings")
    parser.add_argument("--report", required=True, help="Path to assessment HTML report")
    parser.add_argument("--severity", nargs="+", default=["Critical", "High"],
                        help="Severity levels to create issues for (default: Critical High)")
    parser.add_argument("--labels", default="", help="Comma-separated extra labels to add")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be created without creating")
    parser.add_argument("--output", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"Error: Report file not found: {report_path}", file=sys.stderr)
        sys.exit(1)

    html_content = report_path.read_text(encoding="utf-8")
    findings = parse_report_html(html_content)

    if not findings:
        print("No findings extracted from the report.")
        print("Tip: Ensure the report was generated by Azure Environment Advisor.")
        sys.exit(0)

    # Filter by severity
    target_severities = {s.lower() for s in args.severity}
    filtered = [f for f in findings if f.severity.lower() in target_severities]

    extra_labels = [l.strip() for l in args.labels.split(",") if l.strip()]

    print(f"\nAzure Environment Advisor — Issue Creator")
    print(f"{'─'*50}")
    print(f"  Total findings in report: {len(findings)}")
    print(f"  Findings matching severity filter: {len(filtered)}")
    print(f"  Target severities: {', '.join(args.severity)}")
    if args.dry_run:
        print(f"  Mode: DRY RUN (no issues will be created)")
    print(f"{'─'*50}\n")

    if args.output == "json":
        output = []
        for f in filtered:
            output.append({
                "rule_id": f.rule_id,
                "title": f.title,
                "severity": f.severity,
                "pillar": f.pillar,
                "resource": f.resource,
                "issue_title": f"[{f.severity}] {f.rule_id} — {f.title}",
            })
        print(json.dumps(output, indent=2))
        return

    created = 0
    failed = 0
    for finding in filtered:
        success = create_github_issue(finding, extra_labels, dry_run=args.dry_run)
        if success:
            created += 1
        else:
            failed += 1

    print(f"\n{'─'*50}")
    print(f"  {'Would create' if args.dry_run else 'Created'}: {created} issues")
    if failed:
        print(f"  Failed: {failed} issues")
    print(f"{'─'*50}")

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()

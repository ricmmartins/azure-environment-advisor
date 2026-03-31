#!/usr/bin/env python3
"""
Azure Environment Advisor — Rule Validation Script

Validates all rule markdown files in the rules/ directory for:
- Required sections (What to Check, Finding Template, Learn More)
- Proper rule ID format (e.g., SEC-001, REL-010)
- Profile severity coverage in profile files
- Consistent rule catalog across profiles and rules

Usage:
    python scripts/validate-rules.py
    python scripts/validate-rules.py --verbose
    python scripts/validate-rules.py --output json

Exit codes:
    0 = all validations passed
    1 = one or more validations failed
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional


# --- Configuration ---

RULES_DIR = "rules"
PROFILES_DIR = "profiles"
REQUIRED_SECTIONS = ["What to Check", "Finding Template", "Learn More"]
VALID_PILLARS = ["Security", "Reliability", "Cost Optimization", "Operational Excellence", "Performance Efficiency", "Governance"]
VALID_SEVERITIES = ["Critical", "High", "Medium", "Low", "Informational"]
RULE_ID_PATTERN = re.compile(r"^(SEC|REL|COST|OPS|PERF|GOV)-\d{3}$")
PILLAR_PREFIXES = {
    "SEC": "Security",
    "REL": "Reliability",
    "COST": "Cost Optimization",
    "OPS": "Operational Excellence",
    "PERF": "Performance",
    "GOV": "Governance",
}


# --- Data Classes ---

@dataclass
class RuleInfo:
    rule_id: str
    title: str
    file_path: str
    pillar: Optional[str] = None
    severity: Optional[str] = None
    has_what_to_check: bool = False
    has_finding_template: bool = False
    has_learn_more: bool = False
    has_kusto_query: bool = False


@dataclass
class ValidationResult:
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    rules_found: list = field(default_factory=list)
    rules_in_profiles: list = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


# --- Parsing ---

def extract_rules_from_file(file_path: str) -> list[RuleInfo]:
    """Parse a rule markdown file and extract all rules with their metadata."""
    rules = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by H2 headers that match rule ID pattern
    sections = re.split(r"(?=^## )", content, flags=re.MULTILINE)

    for section in sections:
        # Match rule header: ## SEC-001 — Title
        header_match = re.match(r"^## ((?:SEC|REL|COST|OPS|PERF|GOV)-\d{3})\s*[—–-]\s*(.+)", section)
        if not header_match:
            continue

        rule_id = header_match.group(1).strip()
        title = header_match.group(2).strip()

        rule = RuleInfo(
            rule_id=rule_id,
            title=title,
            file_path=file_path,
        )

        # Extract pillar
        pillar_match = re.search(r"\*\*Pillar:\*\*\s*(.+)", section)
        if pillar_match:
            rule.pillar = pillar_match.group(1).strip()

        # Extract severity
        severity_match = re.search(r"\*\*Severity:\*\*\s*(.+)", section)
        if severity_match:
            rule.severity = severity_match.group(1).strip()

        # Check required sections
        rule.has_what_to_check = bool(re.search(r"^### What to Check", section, re.MULTILINE))
        rule.has_finding_template = bool(re.search(r"^### Finding Template", section, re.MULTILINE))
        rule.has_learn_more = bool(re.search(r"^### Learn More", section, re.MULTILINE))

        # Check for KQL/kusto code blocks
        rule.has_kusto_query = bool(re.search(r"```kusto", section))

        rules.append(rule)

    return rules


def extract_rule_ids_from_profile(file_path: str) -> list[str]:
    """Extract rule IDs referenced in a profile's severity adjustment table."""
    rule_ids = []
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all rule IDs in the content
    for match in re.finditer(r"((?:SEC|REL|COST|OPS|PERF|GOV)-\d{3})", content):
        rule_id = match.group(1)
        if rule_id not in rule_ids:
            rule_ids.append(rule_id)

    return rule_ids


# --- Validation ---

def validate(repo_root: str) -> ValidationResult:
    """Run all validations and return results."""
    result = ValidationResult()
    rules_dir = os.path.join(repo_root, RULES_DIR)
    profiles_dir = os.path.join(repo_root, PROFILES_DIR)

    # 1. Collect all rules from rule files
    all_rules: dict[str, RuleInfo] = {}
    rule_files = list(Path(rules_dir).rglob("*.md"))

    if not rule_files:
        result.errors.append(f"No rule files found in {rules_dir}/")
        return result

    for rule_file in sorted(rule_files):
        rel_path = os.path.relpath(rule_file, repo_root)
        try:
            rules = extract_rules_from_file(str(rule_file))
        except (OSError, UnicodeDecodeError) as e:
            result.errors.append(f"Failed to read {rel_path}: {e}")
            continue

        if not rules:
            result.warnings.append(f"No rules found in {rel_path}")
            continue

        for rule in rules:
            rule.file_path = rel_path

            # Check for duplicate rule IDs
            if rule.rule_id in all_rules:
                result.errors.append(
                    f"Duplicate rule ID {rule.rule_id}: found in {all_rules[rule.rule_id].file_path} and {rel_path}"
                )
            else:
                all_rules[rule.rule_id] = rule

            # Validate rule ID format
            if not RULE_ID_PATTERN.match(rule.rule_id):
                result.errors.append(f"{rule.rule_id}: Invalid rule ID format (expected PREFIX-NNN)")

            # Validate pillar matches prefix
            expected_pillar = PILLAR_PREFIXES.get(rule.rule_id.split("-")[0])
            if rule.pillar and expected_pillar and rule.pillar != expected_pillar:
                result.warnings.append(
                    f"{rule.rule_id}: Pillar mismatch — expected '{expected_pillar}', got '{rule.pillar}'"
                )

            # Validate severity (allow conditional severities like "Medium (scale-up), Low (startup)")
            if rule.severity:
                severity_words = re.findall(r"(Critical|High|Medium|Low|Informational)", rule.severity)
                if not severity_words:
                    result.errors.append(
                        f"{rule.rule_id}: Invalid severity '{rule.severity}' (must contain at least one of: {', '.join(VALID_SEVERITIES)})"
                    )
                elif rule.severity not in VALID_SEVERITIES:
                    result.warnings.append(
                        f"{rule.rule_id}: Conditional severity '{rule.severity}' — consider moving conditions to profile files"
                    )

            # Check required sections
            if not rule.has_what_to_check:
                result.errors.append(f"{rule.rule_id}: Missing '### What to Check' section")
            if not rule.has_finding_template:
                result.errors.append(f"{rule.rule_id}: Missing '### Finding Template' section")
            if not rule.has_learn_more:
                result.errors.append(f"{rule.rule_id}: Missing '### Learn More' section")

            # Warn if no KQL query
            if not rule.has_kusto_query:
                result.warnings.append(f"{rule.rule_id}: No KQL query block found (manual/heuristic check)")

    result.rules_found = list(all_rules.keys())

    # 2. Validate profile coverage
    profile_files = list(Path(profiles_dir).glob("*.md")) if os.path.isdir(profiles_dir) else []
    all_profile_rule_ids: set[str] = set()

    if not profile_files:
        result.warnings.append(f"No profile files found in {profiles_dir}/")
    else:
        for profile_file in sorted(profile_files):
            rel_path = os.path.relpath(profile_file, repo_root)
            profile_rule_ids = extract_rule_ids_from_profile(str(profile_file))
            all_profile_rule_ids.update(profile_rule_ids)

            # Check for rule IDs in profiles that don't exist in rules
            for rule_id in profile_rule_ids:
                if rule_id not in all_rules:
                    result.errors.append(
                        f"Profile {rel_path} references {rule_id} which doesn't exist in any rule file"
                    )

    result.rules_in_profiles = sorted(all_profile_rule_ids)

    # Check for rules not covered by any profile
    for rule_id in sorted(all_rules.keys()):
        if rule_id not in all_profile_rule_ids:
            result.warnings.append(f"{rule_id}: Not referenced in any profile severity table")

    return result


# --- Output ---

def print_text_report(result: ValidationResult, verbose: bool = False):
    """Print a human-readable validation report."""
    total_rules = len(result.rules_found)
    print(f"\n{'='*60}")
    print(f"  Azure Environment Advisor — Rule Validation")
    print(f"{'='*60}")
    print(f"\n  Rules found: {total_rules}")
    print(f"  Rules in profiles: {len(result.rules_in_profiles)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")

    if result.errors:
        print(f"\n{'─'*60}")
        print("  ❌ ERRORS")
        print(f"{'─'*60}")
        for error in result.errors:
            print(f"  • {error}")

    if result.warnings and verbose:
        print(f"\n{'─'*60}")
        print("  ⚠️  WARNINGS")
        print(f"{'─'*60}")
        for warning in result.warnings:
            print(f"  • {warning}")

    print(f"\n{'─'*60}")
    if result.passed:
        print("  ✅ ALL VALIDATIONS PASSED")
    else:
        print("  ❌ VALIDATION FAILED")
    print(f"{'─'*60}\n")

    if verbose:
        print("  Rule catalog:")
        for rule_id in sorted(result.rules_found):
            print(f"    {rule_id}")


def print_json_report(result: ValidationResult):
    """Print a JSON validation report."""
    report = {
        "passed": result.passed,
        "rules_found": sorted(result.rules_found),
        "rules_in_profiles": result.rules_in_profiles,
        "errors": result.errors,
        "warnings": result.warnings,
        "summary": {
            "total_rules": len(result.rules_found),
            "total_errors": len(result.errors),
            "total_warnings": len(result.warnings),
        },
    }
    print(json.dumps(report, indent=2))


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Validate Azure Environment Advisor rule files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show warnings and rule catalog")
    parser.add_argument("--output", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--repo-root", default=None, help="Repository root directory (auto-detected if not set)")
    args = parser.parse_args()

    # Auto-detect repo root (script is in scripts/, repo root is parent)
    if args.repo_root:
        repo_root = args.repo_root
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(script_dir)

    if not os.path.isdir(os.path.join(repo_root, RULES_DIR)):
        print(f"Error: {RULES_DIR}/ directory not found in {repo_root}", file=sys.stderr)
        sys.exit(1)

    result = validate(repo_root)

    if args.output == "json":
        print_json_report(result)
    else:
        print_text_report(result, verbose=args.verbose)

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()

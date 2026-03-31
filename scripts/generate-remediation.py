#!/usr/bin/env python3
"""
Azure Environment Advisor — Generate Remediation Files

Reads an assessment baseline JSON and generates ready-to-deploy Bicep files
for each finding that has a remediation template available.

Usage:
    python scripts/generate-remediation.py --baseline baselines/baseline-2026-03-31.json
    python scripts/generate-remediation.py --baseline baselines/baseline-2026-03-31.json --output-dir remediation/generated
    python scripts/generate-remediation.py --baseline baselines/baseline-2026-03-31.json --dry-run
    python scripts/generate-remediation.py --list-templates

Requirements:
    - Python 3.9+
    - No external dependencies (stdlib only)

Exit codes:
    0 = remediation files generated successfully
    1 = error occurred
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


# --- Remediation Template Registry ---

TEMPLATE_DIR = Path(__file__).parent.parent / "remediation" / "bicep"

# Maps rule IDs to their Bicep template filename and required parameters
REMEDIATION_MAP = {
    "SEC-022": {
        "template": "SEC-022-enforce-mfa.bicep",
        "description": "Enforce MFA via Conditional Access policy",
        "scope": "subscription",
        "params": {"excludeGroupIds": "[]"},
    },
    "SEC-014": {
        "template": "SEC-014-remove-public-ip.bicep",
        "description": "Add NSG deny rule for inbound internet traffic",
        "scope": "resourceGroup",
        "params": {"nsgName": "<from-finding>"},
    },
    "SEC-003": {
        "template": "SEC-003-security-contact.bicep",
        "description": "Configure Defender for Cloud security contact",
        "scope": "subscription",
        "params": {"email": "security@company.com", "phone": ""},
    },
    "REL-010": {
        "template": "REL-010-enable-backup.bicep",
        "description": "Create Recovery Services vault and backup policy",
        "scope": "resourceGroup",
        "params": {"vaultName": "rsv-backup", "location": "<from-finding>"},
    },
    "REL-003": {
        "template": "REL-003-storage-replication.bicep",
        "description": "Upgrade storage account from LRS to GRS",
        "scope": "resourceGroup",
        "params": {"storageAccountName": "<from-finding>"},
    },
    "COST-001": {
        "template": "COST-001-create-budget.bicep",
        "description": "Create subscription budget with alert thresholds",
        "scope": "subscription",
        "params": {"budgetName": "monthly-budget", "amount": "1000", "contactEmails": '["admin@company.com"]'},
    },
    "OPS-001": {
        "template": "OPS-001-enable-diagnostics.bicep",
        "description": "Create Log Analytics workspace and Activity Log diagnostics",
        "scope": "resourceGroup",
        "params": {"workspaceName": "law-monitoring", "location": "eastus"},
    },
    "GOV-011": {
        "template": "GOV-011-environment-separation.bicep",
        "description": "Create management group structure for prod/nonprod",
        "scope": "tenant",
        "params": {"rootMgName": "mg-organization"},
    },
}


def list_templates():
    """Print all available remediation templates."""
    print("\nAvailable Remediation Templates")
    print("=" * 70)
    print(f"{'Rule ID':<10} {'Scope':<15} {'Description'}")
    print("-" * 70)
    for rule_id, info in sorted(REMEDIATION_MAP.items()):
        template_path = TEMPLATE_DIR / info["template"]
        status = "✅" if template_path.exists() else "❌ missing"
        print(f"{rule_id:<10} {info['scope']:<15} {info['description']} [{status}]")
    print(f"\nTemplates directory: {TEMPLATE_DIR}")
    print(f"Total: {len(REMEDIATION_MAP)} templates")


def load_baseline(path: str) -> dict:
    """Load a baseline JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_parameter_file(rule_id: str, finding: dict, template_info: dict) -> dict:
    """Generate a Bicep parameter file for a finding."""
    params = {}
    for key, default in template_info["params"].items():
        if default == "<from-finding>":
            # Try to extract from finding's affected resources
            resources = finding.get("affected_resources", [])
            if resources and key.lower() in ["location", "region"]:
                params[key] = {"value": resources[0].get("location", "eastus")}
            elif resources and "name" in key.lower():
                params[key] = {"value": resources[0].get("name", default)}
            else:
                params[key] = {"value": f"TODO-{key}"}
        else:
            # Try to parse JSON arrays/objects
            try:
                params[key] = {"value": json.loads(default)}
            except (json.JSONDecodeError, TypeError):
                params[key] = {"value": default}

    return {
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
        "contentVersion": "1.0.0.0",
        "parameters": params,
    }


def generate_deploy_command(rule_id: str, template_info: dict, params_file: str) -> str:
    """Generate the az deployment command for this remediation."""
    scope = template_info["scope"]
    template = f"remediation/bicep/{template_info['template']}"

    if scope == "subscription":
        return f"az deployment sub create --location eastus --template-file {template} --parameters {params_file}"
    elif scope == "tenant":
        return f"az deployment tenant create --location eastus --template-file {template} --parameters {params_file}"
    else:
        return f"az deployment group create --resource-group <rg-name> --template-file {template} --parameters {params_file}"


def main():
    parser = argparse.ArgumentParser(description="Generate Bicep remediation files from assessment findings")
    parser.add_argument("--baseline", help="Path to assessment baseline JSON file")
    parser.add_argument("--output-dir", default="remediation/generated",
                        help="Output directory for generated files (default: remediation/generated)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without writing files")
    parser.add_argument("--list-templates", action="store_true", help="List all available remediation templates")
    parser.add_argument("--severity", nargs="+", default=["Critical", "High", "Medium"],
                        help="Generate remediation for these severity levels (default: Critical High Medium)")
    args = parser.parse_args()

    if args.list_templates:
        list_templates()
        return

    if not args.baseline:
        print("Error: --baseline is required (or use --list-templates)", file=sys.stderr)
        sys.exit(1)

    baseline_path = Path(args.baseline)
    if not baseline_path.exists():
        print(f"Error: Baseline file not found: {baseline_path}", file=sys.stderr)
        sys.exit(1)

    baseline = load_baseline(str(baseline_path))
    findings = baseline.get("findings", [])

    if not findings:
        print("No findings in baseline — nothing to remediate. 🎉")
        return

    # Filter by severity
    target_severities = {s.lower() for s in args.severity}
    filtered = [f for f in findings if f.get("severity", "").lower() in target_severities]

    output_dir = Path(args.output_dir)

    print(f"\nAzure Environment Advisor — Remediation Generator")
    print(f"{'─' * 55}")
    print(f"  Baseline: {baseline_path}")
    print(f"  Findings: {len(findings)} total, {len(filtered)} matching severity filter")
    print(f"  Output: {output_dir}")
    if args.dry_run:
        print(f"  Mode: DRY RUN")
    print(f"{'─' * 55}\n")

    generated = 0
    skipped = 0

    for finding in filtered:
        rule_id = finding.get("rule_id", "")
        title = finding.get("title", "Unknown")
        severity = finding.get("severity", "Unknown")

        if rule_id not in REMEDIATION_MAP:
            skipped += 1
            continue

        template_info = REMEDIATION_MAP[rule_id]
        template_path = TEMPLATE_DIR / template_info["template"]

        if not template_path.exists():
            print(f"  ⚠️  {rule_id}: Template file missing ({template_info['template']})")
            skipped += 1
            continue

        # Generate parameter file
        params = generate_parameter_file(rule_id, finding, template_info)
        params_filename = f"{rule_id.lower()}-params.json"
        params_path = output_dir / params_filename

        # Generate deploy command
        deploy_cmd = generate_deploy_command(rule_id, template_info, str(params_path))

        if args.dry_run:
            print(f"  [DRY RUN] {rule_id} ({severity}) — {title}")
            print(f"            Template: {template_info['template']}")
            print(f"            Params: {params_filename}")
            print(f"            Deploy: {deploy_cmd}")
            print()
        else:
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(params_path, "w", encoding="utf-8") as f:
                json.dump(params, f, indent=2)

            # Copy deploy instructions
            readme_path = output_dir / f"{rule_id.lower()}-deploy.md"
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(f"# {rule_id} — {title}\n\n")
                f.write(f"**Severity:** {severity}\n")
                f.write(f"**Scope:** {template_info['scope']}\n\n")
                f.write(f"## Deploy\n\n")
                f.write(f"```bash\n{deploy_cmd}\n```\n\n")
                f.write(f"## Review Before Deploying\n\n")
                f.write(f"1. Edit `{params_filename}` to fill in any `TODO-*` values\n")
                f.write(f"2. Validate with: `az bicep build --file remediation/bicep/{template_info['template']}`\n")
                f.write(f"3. Preview changes: add `--what-if` to the deploy command above\n")

            print(f"  ✅ {rule_id} ({severity}) — {title}")
            print(f"     → {params_path}")

        generated += 1

    print(f"\n{'─' * 55}")
    print(f"  Generated: {generated} remediation files")
    print(f"  Skipped: {skipped} (no template available)")
    print(f"  No template: {len(filtered) - generated - skipped} findings")
    print(f"{'─' * 55}")

    if generated > 0 and not args.dry_run:
        print(f"\nNext steps:")
        print(f"  1. Review generated files in {output_dir}/")
        print(f"  2. Edit parameter files to fill in TODO values")
        print(f"  3. Run 'az bicep build' to validate each template")
        print(f"  4. Deploy with --what-if first, then without")


if __name__ == "__main__":
    main()

---
name: azea-full-assessment
description: Run a complete Azure environment assessment — discover resources, determine profile, evaluate all WAF rules, generate an HTML dashboard report, and save a baseline. This is the main entry point for "assess my Azure environment".
license: MIT
metadata:
  author: Azure Environment Advisor
  version: "1.0"
  project: AzureEnvironmentAdvisor
---

Run a complete end-to-end Azure environment assessment by orchestrating all skills in sequence: discover → profile → assess → report → baseline.

**Input**: One or more Azure subscription IDs, subscription names, or a management group ID. Optional flags: include compliance mapping, create GitHub issues, generate trend dashboard.

**Tools required**: Azure MCP Server, ARM MCP Server, File system tools, Terminal

**Reference files**: This skill orchestrates all other `azea-*` skills and their shared references.

---

## Overview

This is the **main entry point** — equivalent to "assess my Azure environment". It chains:

1. **Discover** (`azea-discover`) — Connect and inventory all resources
2. **Profile** (`azea-profile`) — Determine startup / scale-up / enterprise
3. **Assess** (`azea-assess`) — Evaluate all rules with profile-adjusted severity
4. **Report** (`azea-report`) — Generate self-contained HTML dashboard
5. **Baseline** (`azea-baseline`) — Save JSON baseline for drift detection

Optional add-ons (if requested):
6. **Compliance** (`azea-compliance-map`) — Add compliance framework mappings
7. **Remediate** (`azea-remediate`) — Deploy ARM template fixes for findings (opt-in, requires confirmation)
8. **Issues** (`azea-create-issues`) — Create GitHub Issues from findings
9. **Trends** (`azea-baseline` trend mode) — Generate trend dashboard from historical baselines

---

## Steps

### 1. Check Azure Authentication

Follow `.github/skills/shared/procedures/azure-authentication.md`. **HARD GATE** — stop if not authenticated.

### 2. Identify Scope

Accept the user's input:
- **Single subscription**: subscription ID or name
- **Multiple subscriptions**: comma-separated list, or "all"
- **Management group**: management group ID

If not provided, ask:
```
Which Azure subscription would you like me to assess? Provide a subscription ID, name, or management group ID.
```

### 3. Execute Discovery

Run the full discovery process as defined in `.github/skills/azea-discover/SKILL.md`:
- Validate connectivity
- Run all Resource Graph queries (inventory, networking, security, compliance, RBAC)
- Run Log Analytics queries (if workspace available)
- Run additional discovery checks

### 4. Determine Profile

Run the profiling process as defined in `.github/skills/azea-profile/SKILL.md`:
- Compute the 7 profile signals
- Apply the matching algorithm
- Load the profile definition and severity adjustments

### 5. Run Assessment

Run the full assessment as defined in `.github/skills/azea-assess/SKILL.md`:
- Read all rule files from `rules/`
- Evaluate each rule against discovery data
- Apply profile-adjusted severity
- Calculate pillar scores

### 6. Generate Report

Run the report generator as defined in `.github/skills/azea-report/SKILL.md`:
- Build the HTML dashboard from findings
- Write to `assessment-{subscription-name}-{YYYY-MM-DD}.html`

### 7. Save Baseline

Run the baseline save as defined in `.github/skills/azea-baseline/SKILL.md`:
- Serialize findings to JSON
- Write to `baselines/baseline-{subscription-name}-{YYYY-MM-DD}.json`

### 8. Optional: Compliance Mapping

If the user requested compliance mapping (or said "include compliance"):
- Run `.github/skills/azea-compliance-map/SKILL.md`
- Regenerate the report with compliance sections

### 8b. Optional: Remediation

If the user requested remediation (or said "fix findings", "remediate", "deploy fixes"):
- Run `.github/skills/azea-remediate/SKILL.md`
- **HARD GATE** — Requires explicit user confirmation for each deployment
- After remediation, offer to re-run the assessment to verify fixes
- This step is **never automatic** — even in full assessment mode, the user must explicitly request it

### 9. Optional: GitHub Issues

If the user requested issue creation (or said "create issues"):
- Run `.github/skills/azea-create-issues/SKILL.md`
- Default: Critical + High severity only

### 10. Optional: Trend Dashboard

If the user requested trends (or multiple baselines exist and user says "show trends"):
- Run `.github/skills/azea-baseline/SKILL.md` in trend mode

### 11. Multi-Subscription Handling

If multiple subscriptions were specified:
- Repeat Steps 3–7 for each subscription
- Generate a **cross-subscription summary** showing:
  - Total findings by severity across all subscriptions
  - Which subscription has the most critical/high findings
  - Common findings that appear in multiple subscriptions (systemic issues)
  - Overall governance score (average across subscriptions)

### 12. Present Final Summary

```
## Assessment Complete ✅

**Subscription**: <name> (<id>)
**Profile**: <profile> (<team size>)
**Date**: <date>

### Files Generated
- 📄 `assessment-<name>-<date>.html` — Interactive HTML dashboard
- 📦 `baselines/baseline-<name>-<date>.json` — Baseline for drift detection

### Summary
| Severity | Count |
|----------|-------|
| 🔴 Critical | N |
| 🟠 High | N |
| 🟡 Medium | N |
| 🔵 Low | N |
| ✅ Passed | N |

### Pillar Scores
| Pillar | Score |
|--------|-------|
| Security | N% |
| Reliability | N% |
| Cost | N% |
| Operations | N% |
| Performance | N% |
| Governance | N% |

Open the HTML report in any browser to explore findings interactively.

### What's Next?
- `/azea-remediate` — Deploy ARM template fixes for findings (requires Contributor role)
- `/azea-compliance-map` — Add compliance framework mappings to findings
- `/azea-create-issues` — Create GitHub Issues for tracking remediation
- `/azea-baseline` compare — Compare with a previous baseline to detect drift
- Re-run this assessment periodically to track progress
```

---

## Important Guidelines

- **Read-only mode**: Never modify, create, or delete any Azure resource (except via `azea-remediate` with explicit user confirmation)
- **Accuracy**: Only report findings confirmed from actual resource data
- **Tone**: Professional and constructive — advisor, not auditor
- **Completeness**: Assess every rule in `rules/` — skip none
- **Profile awareness**: Always use profile-adjusted severity
- **Specificity**: Use actual resource names, not generic advice

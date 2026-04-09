---
name: azea-create-issues
description: Create GitHub Issues from assessment findings for tracking and remediation. Labels issues by pillar and severity. Supports dry-run mode and severity filtering.
license: MIT
metadata:
  author: Azure Environment Advisor
  version: "1.0"
  project: AzureEnvironmentAdvisor
---

Create GitHub Issues from assessment findings so teams can track and remediate findings through their normal workflow.

**Input**: Assessment findings from `azea-assess`, an HTML report, or a baseline JSON file.

**Tools required**: Terminal (for running Python script), GitHub CLI or API access

**Reference files**:
- `.github/skills/shared/assessment-model.md` — Finding data model
- `scripts/create-issues-from-report.py` — Issue creation script

---

## Steps

### 1. Gather Findings

Use findings from one of:
- A prior `azea-assess` run (in-memory findings)
- An existing HTML report file
- A baseline JSON file from `baselines/`

### 2. Confirm Parameters

#### 2a. Severity filter
By default, create issues only for **Critical** and **High** severity findings.

If the user wants a different filter (e.g., include Medium), confirm:
```
By default, I'll create issues for Critical and High findings only.
Should I also include Medium and/or Low severity findings?
```

#### 2b. Dry run
Offer a dry-run option:
```
Would you like to do a dry run first? This shows what issues would be created without actually creating them.
```

### 3. Create Issues

#### 3a. Using the script
```bash
# Dry run
python scripts/create-issues-from-report.py --report <report-file>.html --dry-run

# Create issues (Critical + High only)
python scripts/create-issues-from-report.py --report <report-file>.html

# Include more severities
python scripts/create-issues-from-report.py --report <report-file>.html --severity Critical High Medium
```

#### 3b. Issue structure
Each issue includes:
- **Title**: `[RULE-ID] Rule Title`
- **Body**: What was found, Why it matters, Recommendation, Resources affected, Learn More links
- **Labels**: `assessment-finding`, `pillar:<name>`, `severity:<level>`

### 4. Present Results

```
## Issues Created

Created **N** GitHub Issues from assessment findings:

| # | Issue | Severity | Pillar | Title |
|---|-------|----------|--------|-------|
| 1 | #42 | 🔴 Critical | Security | SEC-001 — Defender for Cloud not enabled |
| 2 | #43 | 🟠 High | Reliability | REL-003 — No backup policy for SQL databases |
| ... | ... | ... | ... | ... |

**Labels applied**: `assessment-finding`, `pillar:<name>`, `severity:<level>`

Track remediation progress by closing issues as fixes are deployed.
```

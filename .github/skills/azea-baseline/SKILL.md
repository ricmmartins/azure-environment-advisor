---
name: azea-baseline
description: Save assessment results as a JSON baseline for drift detection, compare baselines to find new/resolved findings, and generate trend dashboards showing progress over time.
license: MIT
metadata:
  author: Azure Environment Advisor
  version: "1.0"
  project: AzureEnvironmentAdvisor
---

Save assessment results as JSON baselines, compare them to detect drift, and generate trend dashboards showing progress over time.

**Input**: Assessment findings from `azea-assess` (for saving), or existing baseline files in `baselines/` (for comparison/trends).

**Tools required**: File system tools (read/write JSON), Terminal (for running Python scripts)

**Reference files**:
- `.github/skills/shared/assessment-model.md` — Finding data model
- `baselines/baseline-schema.json` — JSON schema for baseline files
- `baselines/example-baseline.json` — Example baseline for reference
- `scripts/compare-assessments.py` — Baseline comparison script
- `scripts/generate-trend-dashboard.py` — Trend dashboard generator

---

## Steps

### 1. Determine Action

The user may ask to:
- **Save** a baseline from the current assessment
- **Compare** two baselines to detect drift
- **Generate trends** from multiple baselines over time

If unclear, ask:
```
What would you like to do?
1. Save a baseline from the current assessment
2. Compare two baselines (detect drift)
3. Generate a trend dashboard from historical baselines
```

### 2. Save Baseline

#### 2a. Gather assessment data
Use findings, passed checks, and metadata from a prior `azea-assess` run (or run it first if standalone).

#### 2b. Build baseline JSON
Follow the schema in `baselines/baseline-schema.json`:
```json
{
  "metadata": {
    "subscription_id": "...",
    "subscription_name": "...",
    "profile": "...",
    "date": "YYYY-MM-DD",
    "total_resources": N,
    "regions": ["..."]
  },
  "findings": [
    {
      "rule_id": "SEC-001",
      "title": "...",
      "severity": "critical",
      "pillar": "security",
      "resources_affected": ["..."],
      "status": "open"
    }
  ],
  "passed": ["SEC-012", "REL-020", "..."]
}
```

#### 2c. Write baseline file
Save to `baselines/baseline-{subscription-name}-{YYYY-MM-DD}.json`.

Confirm:
```
Baseline saved to `baselines/baseline-<name>-<date>.json`
```

### 3. Compare Baselines (Drift Detection)

#### 3a. Identify baselines
The user provides two baseline files, or the skill auto-detects the two most recent baselines in `baselines/`.

#### 3b. Run comparison
```bash
python scripts/compare-assessments.py --baseline <older>.json --current <newer>.json
```

#### 3c. Present results
The script outputs: new findings, resolved findings, severity changes, and unchanged findings.

### 4. Generate Trend Dashboard

#### 4a. Identify baselines
Check for multiple baseline files in `baselines/`.

#### 4b. Run dashboard generator
```bash
python scripts/generate-trend-dashboard.py --baselines-dir baselines/ --output trend-dashboard.html
```

#### 4c. Present results
```
## Trend Dashboard Generated

📄 **File**: `trend-dashboard.html`
📊 **Baselines analyzed**: N (from <earliest-date> to <latest-date>)

The dashboard shows: score trends, finding counts by severity, pillar breakdown, recurring findings, and executive summary.
```

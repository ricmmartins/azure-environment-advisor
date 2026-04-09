---
name: azea-compliance-map
description: Enrich assessment findings with compliance framework references (SOC2, ISO 27001, HIPAA, PCI-DSS, NIST-CSF) and generate a compliance impact summary.
license: MIT
metadata:
  author: Azure Environment Advisor
  version: "1.0"
  project: AzureEnvironmentAdvisor
---

Map assessment findings to compliance framework controls and generate a compliance impact summary — useful for audit preparation and regulatory awareness.

**Input**: Assessment findings from `azea-assess` (or an existing report/baseline).

**Tools required**: File system tools (to read mapping file)

**Reference files**:
- `.github/skills/shared/assessment-model.md` — Finding data model (includes compliance_refs field)
- `compliance/mapping.json` — Maps each rule ID to framework controls

---

## Steps

### 1. Gather Findings

Use findings from a prior `azea-assess` run, or parse from an existing baseline JSON or HTML report.

### 2. Load Compliance Mapping

Read `compliance/mapping.json`. This file maps each rule ID to controls in:

| Framework | Example Control |
|-----------|----------------|
| **SOC2** | CC6.1 — Logical and Physical Access Controls |
| **ISO 27001** | A.8.20 — Networks security |
| **HIPAA** | §164.312(e)(1) — Transmission Security |
| **PCI-DSS** | 1.3 — Network access to cardholder data environment |
| **NIST-CSF** | PR.AC-5 — Network integrity |

### 3. Enrich Findings

For each finding, look up its rule ID in the mapping and add `compliance_refs`:

```json
{
  "rule_id": "SEC-005",
  "compliance_refs": [
    { "framework": "SOC2", "control": "CC6.1", "description": "Logical and Physical Access Controls" },
    { "framework": "ISO27001", "control": "A.8.20", "description": "Networks security" },
    { "framework": "HIPAA", "control": "§164.312(e)(1)", "description": "Transmission Security" }
  ]
}
```

### 4. Generate Compliance Summary

Build a summary table showing:
- Which frameworks have controls impacted by findings
- Count of impacted controls per framework
- Breakdown by severity

```
## Compliance Impact Summary

| Framework | Impacted Controls | Critical | High | Medium | Low |
|-----------|------------------|----------|------|--------|-----|
| SOC2 | N | N | N | N | N |
| ISO 27001 | N | N | N | N | N |
| HIPAA | N | N | N | N | N |
| PCI-DSS | N | N | N | N | N |
| NIST-CSF | N | N | N | N | N |

> ⚠️ This is a mapping aid to help prioritize remediation for compliance-relevant findings. It is NOT a formal compliance assessment or audit.
```

### 5. Present Per-Finding Compliance

For each finding with compliance mappings, show:
```
**Compliance Impact**:
  • SOC2: CC6.1 — Logical and Physical Access Controls
  • ISO27001: A.8.20 — Networks security
  • HIPAA: §164.312(e)(1) — Transmission Security
```

### 6. Offer Integration

If an HTML report already exists, offer to regenerate it with compliance sections included:
```
Would you like me to regenerate the HTML report with compliance mappings embedded in each finding card?
```

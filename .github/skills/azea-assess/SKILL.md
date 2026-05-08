---
name: azea-assess
description: Evaluate the discovered Azure environment against all Well-Architected Framework rules with profile-adjusted severity. Produces findings, passed checks, and pillar scores.
license: MIT
metadata:
  author: Azure Environment Advisor
  version: "1.0"
  project: AzureEnvironmentAdvisor
---

Evaluate the environment against every rule in `rules/`, applying profile-adjusted severity, and produce a complete set of findings with pillar scores.

**Input**: Discovery data from `azea-discover` and profile from `azea-profile` (preferred). Can self-discover and self-profile if run standalone.

**Tools required**: Azure MCP Server (for additional KQL queries from rules), ARM MCP Server (for dynamic query generation and validation), File system tools (to read rule files)

**Reference files**:
- `.github/skills/shared/assessment-model.md` — Finding data model
- `.github/skills/shared/rule-format.md` — How rules are structured
- `.github/skills/shared/severity-calculation.md` — Scoring methodology
- `.github/skills/shared/procedures/arm-mcp-server.md` — ARM MCP Server tool reference
- `rules/security/*.md` — Security assessment rules
- `rules/reliability/*.md` — Reliability assessment rules
- `rules/cost/*.md` — Cost optimization rules
- `rules/operations/*.md` — Operational excellence rules
- `rules/performance/*.md` — Performance efficiency rules
- `rules/governance/*.md` — Governance and landing zone rules
- `profiles/startup.md` — Startup severity adjustments
- `profiles/scaleup.md` — Scale-up severity adjustments
- `profiles/enterprise.md` — Enterprise severity adjustments

**Shared procedures** (MUST follow):
- `.github/skills/shared/procedures/azure-authentication.md` — Azure session check (only if running standalone)
- `.github/skills/shared/procedures/mcp-query-execution.md` — How to run KQL via MCP

---

## Steps

### 1. Obtain Prerequisites

#### 1a. Discovery data available + profile selected
Use existing data. Skip to Step 2.

#### 1b. Running standalone
Run `azea-discover` steps to gather discovery data, then `azea-profile` steps to determine the profile. Then proceed to Step 2.

### 2. Load Rule Files

Read all rule files from the 6 pillar directories:

| Pillar | Directory | Files |
|--------|-----------|-------|
| Security | `rules/security/` | defender-plans.md, network-security.md, identity.md, secrets.md |
| Reliability | `rules/reliability/` | zone-redundancy.md, high-availability.md, disaster-recovery.md, backup-recovery.md |
| Cost | `rules/cost/` | budget-alerts.md, orphaned-resources.md, right-sizing.md, reservations.md |
| Operations | `rules/operations/` | monitoring.md, policy-governance.md, iac-ci-cd.md, alerting.md |
| Performance | `rules/performance/` | compute-sizing.md, caching.md, database-tiers.md |
| Governance | `rules/governance/` | landing-zone-maturity.md, subscription-topology.md, management-groups.md |

Parse each file to extract individual rules (see `.github/skills/shared/rule-format.md`).

### 3. Load Profile Severity Adjustments

Read the active profile file from `profiles/` and extract the **Severity Adjustments** table. This maps rule IDs to profile-specific severities.

For any rule NOT in the severity adjustments table, use the rule's default severity.

### 4. Evaluate Each Rule

For each rule extracted in Step 2:

#### 4a. Check applicability
If the rule targets a resource type that doesn't exist in the discovery data (e.g., VM rules when no VMs are deployed), mark as **passed** — the rule doesn't apply.

#### 4b. Execute the check
If the rule's "What to Check" section includes a KQL query:
- Execute it against the discovery data or run it via Azure MCP Server
- Follow `.github/skills/shared/procedures/mcp-query-execution.md`

If the rule describes what to check but does **not** include a KQL query:
- Use the ARM MCP Server's `generate_query` tool to create a query from the rule description
- Follow the dynamic generation pipeline in `.github/skills/shared/procedures/mcp-query-execution.md`
- This enables assessment of rules that rely on natural language descriptions rather than pre-written KQL

If the check relies on data already collected during discovery, evaluate against that data directly.

#### 4c. Determine result

- **Finding triggered** (problematic state exists): Create a finding using the Finding Template. Replace placeholders with actual values. Apply the profile-adjusted severity.
- **Pass** (condition not triggered): Add to passed checks list.
- **Cannot evaluate** (data not available): Add to limitations list. Never fabricate findings.

#### 4d. Populate the finding

Following the schema in `.github/skills/shared/assessment-model.md`:
- `rule_id` — from the rule definition
- `title` — from the Finding Template
- `pillar` — from the rule definition
- `severity` — **profile-adjusted** (from Step 3), NOT the default
- `what_found` — factual description with specific resource names
- `why_matters` — business impact from the Finding Template
- `recommendation` — specific, actionable steps
- `resources_affected` — actual resource names and groups
- `learn_more` — Microsoft Learn links from the rule

### 5. Calculate Pillar Scores

Following `.github/skills/shared/severity-calculation.md`:

For each of the 6 pillars:
1. Start at 100%
2. Subtract: Critical = -20, High = -12, Medium = -6, Low = -3
3. Floor at 0%

### 6. Present Assessment Summary

```
## Assessment Complete

**Profile**: <profile> | **Total rules evaluated**: N | **Findings**: N | **Passed**: N | **Limitations**: N

### Findings by Severity
- 🔴 Critical: N
- 🟠 High: N
- 🟡 Medium: N
- 🔵 Low: N
- ✅ Passed: N

### Pillar Scores
| Pillar | Score | Findings |
|--------|-------|----------|
| Security | N% | C critical, H high, M medium, L low |
| Reliability | N% | ... |
| Cost | N% | ... |
| Operations | N% | ... |
| Performance | N% | ... |
| Governance | N% | ... |

**Next step**: Run `/azea-report` to generate the HTML dashboard, or `/azea-full-assessment` for the complete assessment.
```

---

## Important Notes

- Assess **every** rule in `rules/` — don't skip rules even if the environment seems simple
- Always use **profile-adjusted severity**, not the default
- Be specific in findings: "Deploy a Private Endpoint for sql-contoso-prod" not "Consider using Private Endpoints"
- If a rule can't be evaluated, mark it as a limitation — never fabricate findings

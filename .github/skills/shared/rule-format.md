# Rule File Format

Defines how assessment rules in `rules/` are structured. Referenced by `azea-assess` and any skill that reads rule definitions.

---

## Directory Structure

Rules are organized by WAF pillar:

```
rules/
├── security/          # Defender, network security, identity, secrets
│   ├── defender-plans.md
│   ├── network-security.md
│   ├── identity.md
│   └── secrets.md
├── reliability/       # Zone redundancy, backup, HA, DR
│   ├── zone-redundancy.md
│   ├── high-availability.md
│   ├── disaster-recovery.md
│   └── backup-recovery.md
├── cost/              # Budgets, orphaned resources, right-sizing
│   ├── budget-alerts.md
│   ├── orphaned-resources.md
│   ├── right-sizing.md
│   └── reservations.md
├── operations/        # Monitoring, policy, IaC, alerting
│   ├── monitoring.md
│   ├── policy-governance.md
│   ├── iac-ci-cd.md
│   └── alerting.md
├── performance/       # Compute sizing, caching, database tiers
│   ├── compute-sizing.md
│   ├── caching.md
│   └── database-tiers.md
└── governance/        # Landing zone, subscription topology, mgmt groups
    ├── landing-zone-maturity.md
    ├── subscription-topology.md
    └── management-groups.md
```

## Rule Structure

Each markdown file contains **one or more rules**. Each rule follows this structure:

```markdown
## RULE-ID — Rule Title

- **Pillar:** Security / Reliability / Cost / Operations / Performance / Governance
- **Severity:** Critical / High / Medium / Low (this is the default severity)
- **Profiles:** How severity changes per profile (e.g., "Startup: Medium, Scale-up: High, Enterprise: Critical")

### What to Check
Description of what to verify, often with an embedded KQL query in a ```kusto code block.
The KQL query shows what to look for in the discovery data.

### Finding Template
Pre-written text for "What was found", "Why it matters", and "Recommendation"
with placeholders like {resourceName}, {count}, {subscriptionName}.

### Learn More
- [Link title](https://learn.microsoft.com/azure/...) — brief description
```

## Evaluation Process

For each rule:

1. **Read** the rule definition from the corresponding file in `rules/`
2. **Execute** the KQL query from "What to Check" (if present) against the discovery data or via MCP
3. **Evaluate**: If the rule's condition is triggered (problematic state exists), create a finding
4. **Adjust severity**: Look up the profile-adjusted severity from the current profile file in `profiles/`, NOT the default severity in the rule file
5. **Pass**: If the condition is NOT triggered, count it as a passed check
6. **Limitation**: If the rule cannot be evaluated (data not available), note it as a limitation
7. **Populate** the finding using the Finding Template, replacing placeholders with actual values

## Placeholders

Rules use these placeholders in Finding Templates:

| Placeholder | Replaced with |
|-------------|---------------|
| `{subscriptionName}` | Target subscription name |
| `{subscriptionId}` | Target subscription ID |
| `{resourceName}` | Specific resource name |
| `{resourceGroup}` | Resource group name |
| `{count}` | Count of affected resources |
| `{location}` | Azure region |

## Important Notes

- Always use the **profile-adjusted severity**, not the default. A rule that defaults to "Critical" may be "Medium" for startups.
- If a rule doesn't apply (e.g., no VMs deployed), that's a **pass** — don't create a finding.
- Never fabricate findings — only report what you can verify from actual data.
- Each finding should have 1–3 relevant Microsoft Learn documentation links.

# Profile Detection

Defines how to determine the environment profile (startup / scale-up / enterprise) from discovery data. Referenced by `azea-profile` and `azea-full-assessment`.

---

## Signal Thresholds

| Signal | Startup | Scale-up | Enterprise |
|--------|---------|----------|------------|
| Subscriptions | 1–2 | 3–10 | 10+ |
| Management Groups | 0–1 | 1–3 | 3+ nested levels |
| Total Resources | < 50 | 50–500 | 500+ |
| Regions | 1 | 1–2 | 2+ |
| Hub VNet / Firewall | No | Maybe | Yes |
| Resource Groups | 1–5 | 5–20 | 20+ |
| Policy Assignments | 0–5 | 5–20 | 20+ |

## How to Measure Each Signal

Use these queries to compute profile signals from discovery data:

| Signal | Query / Method |
|--------|---------------|
| **Subscriptions** | `resourcecontainers \| where type == 'microsoft.resources/subscriptions' \| summarize count()` |
| **Management Groups** | `resourcecontainers \| where type == 'microsoft.management/managementgroups' \| where name != tenantId \| summarize count()` (exclude Tenant Root Group) |
| **Total Resources** | Use the total from `queries/resource-graph/inventory.kql` |
| **Regions** | `resources \| summarize dcount(location)` |
| **Hub VNet / Firewall** | Check if Azure Firewall exists, or if any VNet name matches patterns like `hub`, `connectivity`, or `transit` |
| **Resource Groups** | `resources \| summarize dcount(resourceGroup)` |
| **Policy Assignments** | `policyresources \| where type == 'microsoft.authorization/policyassignments' \| summarize count()` |

## Matching Algorithm

Count how many of the 7 signals match each profile's thresholds, then:

1. If one profile has **3 or more** matching signals and leads the others → use that profile
2. If two profiles are **tied** (e.g., 3–3–1) → pick the **lower maturity** profile (Startup < Scale-up < Enterprise). It's better to recommend growth than to assume maturity that doesn't exist.
3. If signals are **evenly split** across all three (e.g., 2–2–2 with 1 ambiguous) → default to **Scale-up** as the safe middle ground
4. If **fewer than 3 signals** match any single profile (very unusual) → default to **Startup**

## Profile Files

Load the matching profile from `profiles/` to calibrate severity levels and recommendations:

| Profile | File | Team Size |
|---------|------|-----------|
| Startup | `profiles/startup.md` | 5–50 engineers |
| Scale-up | `profiles/scaleup.md` | 50–200 engineers |
| Enterprise | `profiles/enterprise.md` | 200+ engineers |

## What the Profile Affects

- **Severity adjustments** — Some findings are Critical for enterprise but Medium for startups. Each profile file has a Severity Adjustments table mapping rule IDs to profile-specific severities.
- **Recommendation tone** — Pragmatic for startups, governance-focused for enterprise
- **Expected maturity** — What's reasonable to expect at each stage (e.g., don't suggest PIM for a 5-person startup)

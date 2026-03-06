# Governance Assessment Rules — Subscription Topology

Rules for assessing whether subscription design follows best practices for environment isolation and workload separation.

---

## GOV-010 — All workloads in single subscription

**Pillar:** Governance  
**Severity:** Medium  
**Profiles:** startup: pass, scale-up: Medium, enterprise: High

### What to Check
Count the number of subscriptions and check whether production and non-production resources coexist in the same subscription.

```kusto
resourcecontainers
| where type == "microsoft.resources/subscriptions"
| summarize subCount = count()
```

If only one subscription exists, inspect whether it contains both production and non-production resource groups:

```kusto
resourcecontainers
| where type == "microsoft.resources/subscriptions/resourcegroups"
| extend isProd = name matches regex "(?i)(prod|prd|production)"
| extend isDev = name matches regex "(?i)(dev|test|staging|qa|sandbox|uat)"
| summarize prodGroups = countif(isProd), devGroups = countif(isDev)
```

If `subCount == 1` and both production and non-production resource groups are present, this finding applies.

### Finding Template
**Title:** All workloads deployed in a single subscription  
**What was found:** Only `{subCount}` subscription is in use, containing both production (`{prodGroups}` resource groups) and non-production (`{devGroups}` resource groups) workloads.  
**Why it matters:** A single subscription for all environments creates blast radius risk — a misconfiguration or security breach in development resources can affect production. It also makes it harder to apply differentiated policies, track costs per environment, and manage RBAC boundaries.  
**Recommendation:** Separate production and non-production workloads into dedicated subscriptions. This enables independent RBAC, budget alerts, policy assignments, and reduces the blast radius of changes.

### Learn More
- [Initial Azure subscriptions](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/azure-best-practices/initial-subscriptions) — Guidance on starting with the right number of subscriptions
- [Subscription design and management](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/design-area/resource-org-subscriptions) — Landing zone design area for subscription topology

---

## GOV-011 — No prod/non-prod separation

**Pillar:** Governance  
**Severity:** High  
**Profiles:** startup: Medium, scale-up: High, enterprise: High

### What to Check
Check whether production and development resources share the same resource groups or subscription with no naming or tagging separation.

```kusto
resources
| extend env = tostring(tags["environment"])
| where isempty(env) or env == ""
| summarize untaggedCount = count()
```

```kusto
resourcecontainers
| where type == "microsoft.resources/subscriptions/resourcegroups"
| where not(name matches regex "(?i)(prod|prd|production|dev|test|staging|qa|uat|sandbox)")
| summarize ambiguousGroups = count()
```

If resources lack environment tags and resource group names do not indicate environment separation, this finding applies.

### Finding Template
**Title:** No production/non-production environment separation  
**What was found:** Resources lack `environment` tags and resource group names do not follow a pattern that distinguishes production from non-production. `{untaggedCount}` resources have no environment tag, and `{ambiguousGroups}` resource groups have ambiguous names.  
**Why it matters:** Without environment separation, it is impossible to apply differentiated security policies, manage costs per environment, or ensure that development changes do not impact production. This increases operational risk and makes compliance auditing difficult.  
**Recommendation:** At minimum, apply an `environment` tag (e.g., `prod`, `dev`, `staging`) to all resources and enforce it with Azure Policy. Ideally, separate production and non-production into dedicated subscriptions.

### Learn More
- [Initial Azure subscriptions](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/azure-best-practices/initial-subscriptions) — Recommended subscription strategy for environment separation

---

## GOV-012 — Inconsistent naming convention

**Pillar:** Governance  
**Severity:** Medium  
**Profiles:** startup: Medium, scale-up: Medium, enterprise: Medium

### What to Check
Analyze resource names across the environment for consistency in prefix/suffix patterns, delimiter usage (dashes vs underscores), and inclusion of environment or region identifiers.

```kusto
resources
| extend nameLen = strlen(name)
| extend hasDash = name contains "-"
| extend hasUnderscore = name contains "_"
| extend hasEnvSuffix = name matches regex "(?i)(-|_)(prod|dev|test|staging|qa|uat)(-|_|$)"
| summarize
    totalResources = count(),
    withDash = countif(hasDash),
    withUnderscore = countif(hasUnderscore),
    withEnvSuffix = countif(hasEnvSuffix)
```

If there is a mix of delimiters (both dashes and underscores in significant proportions) or a low percentage of resources with environment identifiers, this finding applies.

### Finding Template
**Title:** Inconsistent resource naming convention  
**What was found:** Out of `{totalResources}` resources, `{withDash}` use dashes and `{withUnderscore}` use underscores as delimiters. Only `{withEnvSuffix}` include an environment identifier in the name. No consistent naming pattern is applied across the environment.  
**Why it matters:** Inconsistent naming makes it harder to identify resource purpose, environment, owner, and region at a glance. It complicates automation, increases the risk of accidental changes to wrong resources, and makes cost management and compliance reporting more difficult.  
**Recommendation:** Adopt the Azure recommended naming convention (e.g., `{resource-type}-{workload}-{environment}-{region}-{instance}`). Enforce naming rules with Azure Policy using pattern-matching `deny` or `audit` effects.

### Learn More
- [Define your naming convention](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/azure-best-practices/resource-naming) — Azure recommended naming convention with examples
- [Develop your naming and tagging strategy](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/azure-best-practices/naming-and-tagging) — Comprehensive guide to naming and tagging for governance

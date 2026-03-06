# Operations Assessment Rules — Policy & Governance

Rules for assessing whether Azure Policy and tagging strategies are in place to enforce organizational standards and maintain environment hygiene.

---

## OPS-010 — No Azure Policy assignments

**Pillar:** Operational Excellence  
**Severity:** High (scale-up/enterprise), Medium (startup)  
**Profiles:** startup: Medium · scale-up: High · enterprise: High

### What to Check
Query Azure Resource Graph for policy assignments on the subscription. If zero assignments exist, there are no automated guardrails enforcing standards.

```kusto
policyresources
| where type == "microsoft.authorization/policyassignments"
| summarize count()
```

### Finding Template
**Title:** No Azure Policy assignments configured  
**What was found:** Subscription `{subscriptionName}` has zero Azure Policy assignments. There are no automated guardrails enforcing security baselines, naming conventions, allowed regions, or resource configurations.  
**Why it matters:** Without Azure Policy, there is no automated enforcement of organizational standards. Developers can deploy resources in any region, use any SKU, skip encryption, or create resources without required tags. This leads to configuration drift, security gaps, and compliance failures that are expensive to remediate retroactively.  
**Recommendation:** Start with built-in policy initiatives such as the Azure Security Benchmark or CIS Microsoft Azure Foundations Benchmark. Begin in Audit mode to assess current compliance, then transition critical policies to Deny mode. Prioritize policies for allowed regions, required tags, and security baselines.

### Learn More
- [Azure Policy overview](https://learn.microsoft.com/azure/governance/policy/overview) — how Azure Policy works, built-in definitions, and enforcement modes
- [Assign a policy using the Azure portal](https://learn.microsoft.com/azure/governance/policy/assign-policy-portal) — quickstart for creating your first policy assignment

---

## OPS-011 — No tagging strategy

**Pillar:** Operational Excellence  
**Severity:** Medium  
**Profiles:** startup: Low · scale-up: Medium · enterprise: High

### What to Check
Evaluate tag coverage across all resources. Check for common organizational tags such as `environment`, `owner`, `cost-center`, `application`, and `team`. Calculate the percentage of resources that have each tag.

```kusto
resources
| extend hasEnvironment = isnotempty(tags.environment) or isnotempty(tags.Environment),
    hasOwner = isnotempty(tags.owner) or isnotempty(tags.Owner),
    hasCostCenter = isnotempty(tags['cost-center']) or isnotempty(tags.CostCenter)
| summarize
    total = count(),
    withEnvironment = countif(hasEnvironment),
    withOwner = countif(hasOwner),
    withCostCenter = countif(hasCostCenter)
| extend
    envCoverage = round(100.0 * withEnvironment / total, 1),
    ownerCoverage = round(100.0 * withOwner / total, 1),
    costCenterCoverage = round(100.0 * withCostCenter / total, 1)
```

### Finding Template
**Title:** Insufficient tagging strategy  
**What was found:** Tag coverage analysis for subscription `{subscriptionName}`: environment tag: {envCoverage}%, owner tag: {ownerCoverage}%, cost-center tag: {costCenterCoverage}%. Out of {total} resources, the majority are missing one or more organizational tags.  
**Why it matters:** Tags are the primary mechanism for cost allocation, ownership tracking, and operational automation in Azure. Without consistent tagging, you cannot accurately attribute costs to teams or projects, identify resource owners during incidents, or automate lifecycle management (e.g., shutting down dev resources at night).  
**Recommendation:** Define a mandatory tagging taxonomy (minimum: `environment`, `owner`, `cost-center`) and enforce it with Azure Policy using the "Require a tag and its value" built-in definition. Apply tags retroactively to existing resources using Azure Policy remediation tasks.

### Learn More
- [Tag resources, resource groups, and subscriptions](https://learn.microsoft.com/azure/azure-resource-manager/management/tag-resources) — how tagging works and best practices for tag design
- [Tutorial: Govern tags with Azure Policy](https://learn.microsoft.com/azure/governance/policy/tutorials/govern-tags) — step-by-step guide to enforcing tags with policy

---

## OPS-012 — Non-compliant policy resources

**Pillar:** Operational Excellence  
**Severity:** High (if > 20% non-compliant)  
**Profiles:** startup: Low · scale-up: Medium · enterprise: High

### What to Check
Query Azure Resource Graph for policy compliance state. Calculate the percentage of non-compliant resources across all active policy assignments.

```kusto
policyresources
| where type == "microsoft.policyinsights/policystates"
| where tostring(properties.complianceState) == "NonCompliant"
| summarize nonCompliantCount = count() by
    policyName = tostring(properties.policyDefinitionName),
    policyAssignment = tostring(properties.policyAssignmentName)
| order by nonCompliantCount desc
```

### Finding Template
**Title:** High rate of policy non-compliance  
**What was found:** Subscription `{subscriptionName}` has {nonCompliantCount} non-compliant resource(s) across {assignmentCount} policy assignment(s), representing {nonCompliantPercentage}% non-compliance. Top non-compliant policies: {policyList}.  
**Why it matters:** A high non-compliance rate indicates that organizational standards are not being met, either because policies are set to Audit-only mode without follow-up remediation, or because teams are not aware of the requirements. Non-compliant resources may have security vulnerabilities, missing encryption, or configuration drift.  
**Recommendation:** Remediate non-compliant resources starting with the highest-severity policies. Use Azure Policy remediation tasks for policies that support automatic remediation. For persistent non-compliance, consider transitioning policies from Audit to Deny mode to prevent new violations.

### Learn More
- [Remediate non-compliant resources](https://learn.microsoft.com/azure/governance/policy/how-to/remediate-resources) — how to create and manage remediation tasks for policy violations

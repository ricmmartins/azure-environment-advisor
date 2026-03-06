# Governance Assessment Rules — Management Groups

Rules for assessing whether management group hierarchy and policy assignment follow Azure landing zone best practices.

---

## GOV-020 — No management group hierarchy

**Pillar:** Governance  
**Severity:** Medium  
**Profiles:** startup (1 subscription): pass, scale-up: Medium, enterprise: High

### What to Check
Query for custom management groups beyond the Tenant Root Group. If only the default Tenant Root Group exists, there is no hierarchy.

```kusto
resourcecontainers
| where type == "microsoft.management/managementgroups"
| where name != tenantId
| summarize customMgCount = count()
```

If `customMgCount == 0`, this finding applies.

### Finding Template
**Title:** No management group hierarchy configured  
**What was found:** The tenant has no custom management groups. All subscriptions sit directly under the Tenant Root Group with no organizational hierarchy.  
**Why it matters:** Without management groups, policies and RBAC must be assigned per subscription, leading to inconsistent governance as subscriptions are added. Management groups enable centralized policy enforcement, consistent access control, and logical organization of subscriptions by environment, workload, or business unit.  
**Recommendation:** Create a basic management group hierarchy following the Azure landing zone pattern: an intermediate root group, then child groups for Platform (Connectivity, Identity, Management) and Landing Zones (Production, Non-production), plus a Sandbox group for experimentation.

### Learn More
- [Azure management groups overview](https://learn.microsoft.com/azure/governance/management-groups/overview) — How management groups organize subscriptions and enable hierarchical governance
- [Resource organization with management groups](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/design-area/resource-org-management-groups) — Landing zone design guidance for management group hierarchy

---

## GOV-021 — Policies not assigned at management group level

**Pillar:** Governance  
**Severity:** Medium  
**Profiles:** startup: Medium, scale-up: Medium, enterprise: Medium

### What to Check
Check whether Azure Policy assignments exist at the management group scope or only at the subscription level. If management groups exist but all policies are assigned to individual subscriptions, governance is not centralized.

```kusto
policyresources
| where type == "microsoft.authorization/policyassignments"
| extend scope = tostring(properties.scope)
| extend isManagementGroupScope = scope contains "/providers/Microsoft.Management/managementGroups/"
| extend isSubscriptionScope = scope matches regex "^/subscriptions/[^/]+$"
| summarize
    mgAssignments = countif(isManagementGroupScope),
    subAssignments = countif(isSubscriptionScope)
```

If `mgAssignments == 0` and `subAssignments > 0`, this finding applies.

### Finding Template
**Title:** Azure Policies assigned only at subscription level  
**What was found:** `{subAssignments}` policy assignments exist at the subscription scope, but `{mgAssignments}` are assigned at the management group level. Governance policies are not centrally enforced.  
**Why it matters:** Subscription-level policy assignments must be duplicated across every subscription, increasing management overhead and the risk of drift. When new subscriptions are created, they inherit no baseline policies unless assignments are manually replicated. Management group-level assignments automatically apply to all child subscriptions.  
**Recommendation:** Move baseline governance policies (e.g., allowed regions, required tags, diagnostic settings, denied resource types) to the appropriate management group level. Keep workload-specific policies at the subscription or resource group level.

### Learn More
- [Azure Policy overview](https://learn.microsoft.com/azure/governance/policy/overview) — How Azure Policy enforces organizational standards and compliance
- [Manage your resources with management groups](https://learn.microsoft.com/azure/governance/management-groups/manage) — How to assign policies and RBAC at the management group scope

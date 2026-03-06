# Governance Assessment Rules — Landing Zone Maturity

Rules for assessing the presence and maturity of Azure landing zone architecture in the environment.

---

## GOV-001 — No landing zone structure detected

**Pillar:** Governance  
**Severity:** High  
**Profiles:** startup: Medium, scale-up: High, enterprise: High

### What to Check
Evaluate whether the environment has any landing zone structural elements: custom management groups, multiple subscriptions, hub virtual network, or Azure Policy assignments beyond built-in defaults.

```kusto
resourcecontainers
| where type == "microsoft.management/managementgroups"
| where name != tenantId
| summarize mgCount = count()
```

```kusto
resourcecontainers
| where type == "microsoft.resources/subscriptions"
| summarize subCount = count()
```

```kusto
resources
| where type == "microsoft.network/virtualnetworks"
| where name matches regex "(?i)(hub|connectivity|transit)"
| summarize hubCount = count()
```

```kusto
policyresources
| where type == "microsoft.authorization/policyassignments"
| summarize policyCount = count()
```

If custom management groups = 0, subscriptions = 1, hub VNets = 0, and policy assignments are minimal or zero, this finding applies.

### Finding Template
**Title:** No landing zone structure detected  
**What was found:** The environment has no custom management groups, a single subscription, no hub network, and no meaningful Azure Policy assignments. There is no landing zone architecture in place.  
**Why it matters:** Without a landing zone, environments lack governance guardrails, network segmentation, and consistent security baselines. This makes it difficult to scale securely, onboard new workloads, or meet compliance requirements as the organization grows.  
**Recommendation:** Adopt a landing zone architecture appropriate for your maturity level. Startup → Start with the Startup Scale Landing Zone (startupscalelanding.zone). Scale-up → Follow the Trey Research pattern with hub-spoke networking. Enterprise → Deploy the full Azure Landing Zone (ALZ) accelerator.

### Learn More
- [What is an Azure landing zone?](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/) — Overview of landing zone concepts, design areas, and implementation options
- [Start with a landing zone](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/starter-landing-zone) — Lightweight starter landing zone for organizations beginning their cloud journey

---

## GOV-002 — Landing zone maturity gap

**Pillar:** Governance  
**Severity:** Medium  
**Profiles:** startup: Medium, scale-up: Medium, enterprise: Medium

### What to Check
Evaluate whether landing zone elements are partially implemented. For example, management groups exist but have no policy assignments, or a hub VNet exists but has no firewall or gateway.

Check for management groups without policies:

```kusto
resourcecontainers
| where type == "microsoft.management/managementgroups"
| where name != tenantId
| project mgName = name, mgId = id
```

Cross-reference with policy assignments at the management group scope:

```kusto
policyresources
| where type == "microsoft.authorization/policyassignments"
| where id contains "/providers/Microsoft.Management/managementGroups/"
| summarize policyCount = count() by managementGroupId = tostring(split(id, "/providers/Microsoft.Authorization")[0])
```

If management groups exist but have zero or very few policy assignments, this finding applies.

### Finding Template
**Title:** Landing zone maturity gap detected  
**What was found:** Some landing zone elements are present (e.g., custom management groups, multiple subscriptions) but key components are missing or incomplete — such as policy assignments, network security controls, or centralized logging.  
**Why it matters:** A partially implemented landing zone creates a false sense of governance. Without policies enforcing standards, management groups serve only as organizational folders. Without hub networking, spoke workloads cannot securely share services or egress through centralized inspection.  
**Recommendation:** Identify gaps against the appropriate landing zone reference architecture. Prioritize: (1) baseline policy assignments on management groups, (2) centralized logging to a Log Analytics workspace, (3) hub-spoke network topology with DNS and egress controls.

### Learn More
- [Landing zone design principles](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/design-principles) — Core principles for Azure landing zone architecture
- [Enterprise-scale architecture](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/enterprise-scale/architecture) — Reference architecture for enterprise-grade landing zones

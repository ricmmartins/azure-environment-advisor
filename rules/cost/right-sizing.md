# Cost Assessment Rules — Right-Sizing

Rules for assessing whether Azure resources are appropriately sized for their workloads.

---

## COST-020 — Over-provisioned VMs

**Pillar:** Cost Optimization  
**Severity:** Medium  
**Profiles:** startup: Medium · scale-up: Medium · enterprise: Medium

### What to Check
Reference Azure Advisor cost recommendations for right-sizing suggestions. Alternatively, check Azure Monitor metrics for VMs with consistently low CPU utilization (average < 5% over 14 days) or low memory usage, which indicate over-provisioning.

```kusto
advisorresources
| where type == "microsoft.advisor/recommendations"
| where tostring(properties.category) == "Cost"
| where tostring(properties.shortDescription.solution) contains "size" or
    tostring(properties.shortDescription.solution) contains "resize"
| project name, resourceGroup,
    impactedResource = tostring(properties.resourceMetadata.resourceId),
    annualSavings = tostring(properties.extendedProperties.annualSavingsAmount),
    currentSku = tostring(properties.extendedProperties.currentSku),
    targetSku = tostring(properties.extendedProperties.targetSku)
```

### Finding Template
**Title:** Over-provisioned VMs detected  
**What was found:** Found {count} VM(s) flagged as over-provisioned in subscription `{subscriptionName}`. Potential annual savings: ~${totalSavings}. Top candidates: {vmList}.  
**Why it matters:** Over-provisioned VMs waste compute spend on capacity that is never used. In many environments, VMs are initially sized for peak demand but never right-sized after deployment, leading to 30-70% wasted compute spend.  
**Recommendation:** Resize VMs to match actual utilization patterns. For dev/test workloads with variable CPU needs, consider switching to B-series burstable VMs which offer lower baseline cost with the ability to burst when needed.

### Learn More
- [Azure Advisor cost recommendations](https://learn.microsoft.com/azure/advisor/advisor-cost-recommendations) — automated right-sizing recommendations based on usage telemetry
- [Azure VM sizes](https://learn.microsoft.com/azure/virtual-machines/sizes) — full catalog of VM families and their intended workloads

---

## COST-021 — Dev/test resources using production SKUs

**Pillar:** Cost Optimization  
**Severity:** Medium  
**Profiles:** startup: Low · scale-up: Medium · enterprise: Medium

### What to Check
Identify resources in resource groups whose names contain "dev", "test", or "staging" that are using premium or production-tier SKUs. Check for Premium SSD disks, Premium-tier databases, and high-end VM sizes in non-production environments.

```kusto
resources
| where resourceGroup contains "dev" or resourceGroup contains "test"
    or resourceGroup contains "staging" or resourceGroup contains "sandbox"
| where (type == "microsoft.compute/virtualmachines"
        and tostring(properties.hardwareProfile.vmSize) !startswith "Standard_B")
    or (type == "microsoft.sql/servers/databases"
        and tostring(sku.tier) in ("Premium", "BusinessCritical"))
    or (type == "microsoft.compute/disks"
        and tostring(sku.name) startswith "Premium")
| project name, type, resourceGroup,
    sku = coalesce(tostring(sku.name), tostring(properties.hardwareProfile.vmSize))
```

### Finding Template
**Title:** Dev/test resources using production-tier SKUs  
**What was found:** Found {count} resource(s) in non-production resource groups using premium or production-tier SKUs in subscription `{subscriptionName}`. Resources: {resourceList}.  
**Why it matters:** Non-production environments typically do not require the same performance guarantees as production. Using premium SKUs for dev/test workloads wastes budget that could be redirected to production reliability or innovation.  
**Recommendation:** Downgrade non-production resources to Basic or Standard tiers. Use B-series burstable VMs for dev/test compute, Standard SSD instead of Premium SSD for disks, and General Purpose tier instead of Business Critical for databases.

### Learn More
- [What is Azure Dev/Test?](https://learn.microsoft.com/azure/devtest/what-is-devtest) — discounted pricing and configurations for non-production workloads
- [Azure SQL service tiers](https://learn.microsoft.com/azure/azure-sql/database/service-tiers-general-purpose-business-critical) — comparison of General Purpose vs Business Critical tiers

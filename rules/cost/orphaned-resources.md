# Cost Assessment Rules — Orphaned Resources

Rules for assessing whether unused or orphaned resources are wasting Azure spend.

---

## COST-010 — Unattached managed disks

**Pillar:** Cost Optimization  
**Severity:** Low (< 5 disks), Medium (≥ 5 disks)  
**Profiles:** startup: Low · scale-up: Medium · enterprise: Medium

### What to Check
Query Azure Resource Graph for managed disks where `managedBy` is empty, indicating the disk is not attached to any VM. Estimate monthly waste based on disk tier and size.

```kusto
resources
| where type == "microsoft.compute/disks"
| where isempty(managedBy)
| project name, resourceGroup, location,
    sku = tostring(sku.name),
    sizeGb = tostring(properties.diskSizeGB),
    timeCreated = tostring(properties.timeCreated)
```

### Finding Template
**Title:** Unattached managed disks found  
**What was found:** Found {count} managed disk(s) not attached to any VM across subscription `{subscriptionName}`. Estimated monthly waste: ~${estimatedCost}/month based on disk tiers and sizes.  
**Why it matters:** Unattached disks continue to incur storage charges even when no VM is using them. They are commonly left behind after VM deletions or failed deployments and can accumulate significant costs over time.  
**Recommendation:** Review each unattached disk. If the data is still needed, create a snapshot for long-term retention then delete the disk. If the data is no longer needed, delete the disk directly.

### Learn More
- [Find and delete unattached managed disks](https://learn.microsoft.com/azure/virtual-machines/disks-find-unattached-portal) — how to locate and clean up orphaned disks in the Azure portal

---

## COST-011 — Orphaned public IP addresses

**Pillar:** Cost Optimization  
**Severity:** Low  
**Profiles:** startup: Low · scale-up: Low · enterprise: Low

### What to Check
Query Azure Resource Graph for public IP addresses not associated with any NIC or resource. Each unused static public IP costs approximately $3.65/month.

```kusto
resources
| where type == "microsoft.network/publicipaddresses"
| where isempty(properties.ipConfiguration)
    and isempty(properties.natGateway)
| project name, resourceGroup, location,
    allocationMethod = tostring(properties.publicIPAllocationMethod),
    ipAddress = tostring(properties.ipAddress)
```

### Finding Template
**Title:** Orphaned public IP addresses found  
**What was found:** Found {count} public IP address(es) not associated with any resource in subscription `{subscriptionName}`. Estimated waste: ~${count × 3.65}/month for static IPs.  
**Why it matters:** Unassociated public IP addresses incur charges (~$3.65/month each for static IPs) and expand your attack surface unnecessarily. They are commonly left behind after deleting VMs, load balancers, or other resources.  
**Recommendation:** Delete unneeded public IP addresses. If the IP must be preserved for future use, document the reason and set a calendar reminder to re-evaluate.

### Learn More
- [Public IP addresses overview](https://learn.microsoft.com/azure/virtual-network/ip-services/virtual-network-public-ip-address) — pricing, allocation methods, and lifecycle management for Azure public IPs

---

## COST-012 — Idle Network Interfaces

**Pillar:** Cost Optimization  
**Severity:** Low  
**Profiles:** startup: Low · scale-up: Low · enterprise: Low

### What to Check
Query Azure Resource Graph for NICs not attached to any VM. While NICs themselves are free, they often retain associated public IPs and NSGs, adding clutter and potential cost.

```kusto
resources
| where type == "microsoft.network/networkinterfaces"
| where isempty(properties.virtualMachine)
| project name, resourceGroup, location,
    hasPublicIp = isnotempty(properties.ipConfigurations[0].properties.publicIPAddress)
```

### Finding Template
**Title:** Idle network interfaces found  
**What was found:** Found {count} network interface(s) not attached to any VM in subscription `{subscriptionName}`. {withPublicIpCount} of these have associated public IP addresses.  
**Why it matters:** Orphaned NICs create management clutter and may retain associated public IPs that incur charges. They are commonly left behind after VM deletions and make it harder to maintain a clean, auditable environment.  
**Recommendation:** Review and delete idle NICs that are no longer needed. Check whether they have associated public IPs or NSGs that should also be cleaned up.

### Learn More
- [Azure best practices for cost management](https://learn.microsoft.com/azure/cost-management-billing/costs/cost-mgt-best-practices)
- [Virtual network interface cards overview](https://learn.microsoft.com/azure/virtual-network/virtual-network-network-interface)

---

## COST-013 — Empty resource groups

**Pillar:** Cost Optimization  
**Severity:** Low  
**Profiles:** startup: Low · scale-up: Low · enterprise: Low

### What to Check
Query Azure Resource Graph to identify resource groups that contain zero resources.

```kusto
resourcecontainers
| where type == "microsoft.resources/subscriptions/resourcegroups"
| join kind=leftouter (
    resources
    | summarize resourceCount = count() by resourceGroup = tostring(resourceGroup),
        subscriptionId
) on $left.name == $right.resourceGroup, subscriptionId
| where isnull(resourceCount) or resourceCount == 0
| project name, subscriptionId, location, tags
```

### Finding Template
**Title:** Empty resource groups found  
**What was found:** Found {count} resource group(s) with no resources in subscription `{subscriptionName}`.  
**Why it matters:** While empty resource groups do not incur direct costs, they add management overhead, make it harder to navigate the environment, and may indicate incomplete cleanup after resource deletions or failed deployments.  
**Recommendation:** Review and delete empty resource groups that are no longer needed. Verify they are not placeholders for upcoming deployments before deleting.

### Learn More
- [Azure best practices for cost management](https://learn.microsoft.com/azure/cost-management-billing/costs/cost-mgt-best-practices)
- [Manage Azure resource groups](https://learn.microsoft.com/azure/azure-resource-manager/management/manage-resource-groups-portal)

# Performance Assessment Rules — Compute Sizing

Rules for assessing whether compute resources are appropriately sized and using current-generation SKUs.

---

## PERF-001 — App Service using Basic tier in production

**Pillar:** Performance  
**Severity:** Medium  
**Profiles:** startup: Low, scale-up: Medium, enterprise: Medium

### What to Check
Query App Service Plans where `sku.tier == "Basic"` in resource groups that follow production naming patterns (e.g., contain `prod`, `prd`, or `production`).

```kusto
resources
| where type == "microsoft.web/serverfarms"
| where sku.tier == "Basic"
| where resourceGroup matches regex "(?i)(prod|prd|production)"
| project name, resourceGroup, subscriptionId, sku.name, sku.tier
```

### Finding Template
**Title:** App Service Plan on Basic tier in production  
**What was found:** App Service Plan `{name}` in resource group `{resourceGroup}` is running on Basic tier (`{sku.name}`).  
**Why it matters:** Basic tier lacks autoscaling, deployment slots, and VNet integration — features critical for production reliability, zero-downtime deployments, and network security.  
**Recommendation:** Upgrade to Standard (S1) or Premium (P1v3) tier. Standard adds autoscale and deployment slots; Premium adds VNet integration and better performance.

### Learn More
- [App Service hosting plans overview](https://learn.microsoft.com/azure/app-service/overview-hosting-plans) — Compare features and limits across App Service tiers
- [Scale up an app in Azure App Service](https://learn.microsoft.com/azure/app-service/manage-scale-up) — Steps to change the pricing tier of an App Service Plan

---

## PERF-002 — VM using previous generation size

**Pillar:** Performance  
**Severity:** Low  
**Profiles:** startup: Low, scale-up: Low, enterprise: Low

### What to Check
Query VMs using previous-generation sizes such as Dv2, Dv3, Av1, or Av2 series instead of current-generation Dv4, Dv5, or Dasv5.

```kusto
resources
| where type == "microsoft.compute/virtualmachines"
| extend vmSize = tostring(properties.hardwareProfile.vmSize)
| where vmSize matches regex "(?i)(Standard_(A[0-9]|D[0-9]+s?_v[23]|DS[0-9]+_v[23]))"
| project name, resourceGroup, subscriptionId, vmSize
```

### Finding Template
**Title:** VM using previous-generation size  
**What was found:** VM `{name}` in resource group `{resourceGroup}` is using size `{vmSize}`, which is a previous-generation SKU.  
**Why it matters:** Previous-generation VM sizes offer lower performance per cost compared to current generations. Newer series (Dv4, Dv5, Dasv5) provide better compute performance, memory bandwidth, and price-performance ratios.  
**Recommendation:** Migrate to the latest generation equivalent (e.g., Dv3 → Dv4 or Dv5, A-series → Dasv5). Test workload compatibility before migrating.

### Learn More
- [Azure VM sizes](https://learn.microsoft.com/azure/virtual-machines/sizes) — Full listing of available VM sizes by family
- [Sizes overview for VMs in Azure](https://learn.microsoft.com/azure/virtual-machines/sizes-overview) — Guidance on choosing the right VM size family for your workload

---

## PERF-003 — AKS using default node pool only

**Pillar:** Performance  
**Severity:** Medium  
**Profiles:** startup: Low, scale-up: Medium, enterprise: Medium

### What to Check
Query AKS clusters that have only a single node pool, meaning system and user workloads share the same pool with no isolation.

```kusto
resources
| where type == "microsoft.containerservice/managedclusters"
| extend poolCount = array_length(properties.agentPoolProfiles)
| where poolCount == 1
| project name, resourceGroup, subscriptionId, poolCount
```

### Finding Template
**Title:** AKS cluster using a single node pool  
**What was found:** AKS cluster `{name}` in resource group `{resourceGroup}` has only `{poolCount}` node pool. System components and user workloads share the same pool.  
**Why it matters:** Running system pods (CoreDNS, metrics-server) alongside application workloads on the same node pool creates resource contention and makes it harder to scale, patch, or right-size independently.  
**Recommendation:** Add a dedicated user node pool for application workloads. Keep the system pool small (e.g., Standard_D2s_v5) with taints to prevent user pod scheduling.

### Learn More
- [Use system node pools in AKS](https://learn.microsoft.com/azure/aks/use-system-pools) — Requirements and best practices for system node pools
- [Create and manage multiple node pools in AKS](https://learn.microsoft.com/azure/aks/use-multiple-node-pools) — How to add and configure user node pools

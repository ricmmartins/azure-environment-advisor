# Reliability Assessment Rules — Zone Redundancy

Rules for assessing whether Azure resources are configured for zone-redundant deployments to survive availability zone failures.

---

## REL-001 — Azure SQL not zone-redundant

**Pillar:** Reliability
**Severity:** High
**Profiles:** enterprise: High · scale-up: High · startup: Medium

### What to Check
SQL databases on General Purpose (vCore) or Business Critical tier with `zoneRedundant` set to `false`.

```kusto
resources
| where type == "microsoft.sql/servers/databases"
| where properties.currentSku.tier in ("GeneralPurpose", "BusinessCritical")
| where properties.zoneRedundant == false
| project name, resourceGroup, location, sku=properties.currentSku.tier, zoneRedundant=properties.zoneRedundant
```

### Finding Template
**Title:** Azure SQL Database is not zone-redundant
**What was found:** SQL database `{name}` in resource group `{resourceGroup}` is running on the `{sku}` tier without zone redundancy enabled.
**Why it matters:** Without zone redundancy, a single availability zone outage can cause database downtime. Zone-redundant deployments replicate data synchronously across zones, providing automatic failover with zero data loss during zone failures.
**Recommendation:** Enable zone redundancy for this database. On the General Purpose vCore tier, zone redundancy is available at no additional cost. For Business Critical tier, zone-redundant configuration ensures both compute and storage are spread across zones.

### Learn More
- [High availability for Azure SQL Database](https://learn.microsoft.com/azure/azure-sql/database/high-availability-sla) — Overview of high-availability architecture and SLA guarantees
- [Reliability in Azure SQL Database](https://learn.microsoft.com/azure/reliability/reliability-sql-database) — Zone redundancy and disaster recovery guidance

---

## REL-002 — App Service not zone-redundant

**Pillar:** Reliability
**Severity:** High
**Profiles:** enterprise: High · scale-up: Medium · startup: Low

### What to Check
App Service Plans with `zoneRedundant` set to `false`. Zone redundancy requires a minimum of 3 instances.

```kusto
resources
| where type == "microsoft.web/serverfarms"
| where properties.zoneRedundant == false
| project name, resourceGroup, location, sku=sku.name, instances=properties.numberOfWorkers, zoneRedundant=properties.zoneRedundant
```

### Finding Template
**Title:** App Service Plan is not zone-redundant
**What was found:** App Service Plan `{name}` in resource group `{resourceGroup}` is not configured for zone redundancy. Current instance count: `{instances}`.
**Why it matters:** A non-zone-redundant App Service Plan runs all instances within a single availability zone. If that zone experiences an outage, all hosted apps become unavailable. Zone-redundant deployments distribute instances across three zones automatically.
**Recommendation:** Enable zone redundancy for the App Service Plan. This requires a minimum of 3 instances to ensure at least one instance per zone. Zone redundancy must be set at plan creation time — migration may require creating a new plan.

### Learn More
- [Reliability in Azure App Service](https://learn.microsoft.com/azure/reliability/reliability-app-service) — Zone redundancy support and configuration
- [Azure App Service plan overview](https://learn.microsoft.com/azure/app-service/overview-hosting-plans) — Plan tiers and scaling options

---

## REL-003 — Storage not using ZRS/GRS

**Pillar:** Reliability
**Severity:** High
**Profiles:** enterprise: High · scale-up: Medium · startup: Medium

### What to Check
Storage accounts configured with locally redundant storage (LRS), which keeps all copies in a single data center.

```kusto
resources
| where type == "microsoft.storage/storageaccounts"
| where sku.name has "LRS"
| project name, resourceGroup, location, redundancy=sku.name, kind=kind
```

### Finding Template
**Title:** Storage account uses locally redundant storage (LRS) only
**What was found:** Storage account `{name}` in resource group `{resourceGroup}` is configured with `{redundancy}`, which stores all replicas in a single data center.
**Why it matters:** LRS provides only 99.999999999% (11 nines) durability within a single data center. A data center-level failure (fire, flood, power) could result in permanent data loss. ZRS provides durability across three availability zones; GRS/GZRS adds cross-region protection.
**Recommendation:** Upgrade to zone-redundant storage (ZRS) for in-region redundancy across availability zones. For critical data requiring cross-region protection, use geo-redundant storage (GRS) or geo-zone-redundant storage (GZRS).

### Learn More
- [Azure Storage redundancy](https://learn.microsoft.com/azure/storage/common/storage-redundancy) — Comparison of LRS, ZRS, GRS, GZRS options
- [Reliability in Azure Storage](https://learn.microsoft.com/azure/reliability/reliability-storage-accounts) — Best practices for storage availability

---

## REL-004 — AKS not using availability zones

**Pillar:** Reliability
**Severity:** High
**Profiles:** enterprise: High · scale-up: Medium · startup: Low

### What to Check
AKS clusters with node pools not spread across availability zones.

```kusto
resources
| where type == "microsoft.containerservice/managedclusters"
| mv-expand pool = properties.agentPoolProfiles
| where isnull(pool.availabilityZones) or array_length(pool.availabilityZones) < 3
| project clusterName=name, resourceGroup, location, poolName=pool.name, zones=pool.availabilityZones
```

### Finding Template
**Title:** AKS node pool is not spread across availability zones
**What was found:** AKS cluster `{clusterName}` has node pool `{poolName}` in resource group `{resourceGroup}` that is not configured to use availability zones (current zones: `{zones}`).
**Why it matters:** Without availability zone distribution, a single zone outage can take down all nodes in the pool, causing application downtime. Zone-spread node pools ensure pods can be rescheduled to healthy nodes in other zones automatically.
**Recommendation:** Configure node pools to span 3 availability zones. Availability zones must be set at node pool creation time — existing pools cannot be migrated. Create new zone-redundant node pools and cordon/drain the old ones. Ensure pod disruption budgets and topology spread constraints are configured for zone-aware scheduling.

### Learn More
- [Use availability zones in AKS](https://learn.microsoft.com/azure/aks/availability-zones) — Configuring AKS node pools across zones
- [Reliability in Azure Kubernetes Service](https://learn.microsoft.com/azure/reliability/reliability-kubernetes) — Best practices for AKS availability

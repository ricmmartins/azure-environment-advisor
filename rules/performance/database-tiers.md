# Performance Assessment Rules — Database Tiers

Rules for assessing whether database resources are on appropriate service tiers and purchasing models for their workload profile.

---

## PERF-020 — SQL Database using DTU model

**Pillar:** Performance  
**Severity:** Medium  
**Profiles:** startup: Low, scale-up: Medium, enterprise: Medium

### What to Check
Query SQL databases that use DTU-based service tiers (Basic, Standard, Premium) rather than the vCore purchasing model.

```kusto
resources
| where type == "microsoft.sql/servers/databases"
| where properties.currentServiceObjectiveName matches regex "(?i)^(Basic|S[0-9]+|P[0-9]+)$"
| where name != "master"
| project name, resourceGroup, subscriptionId,
    serviceTier = tostring(properties.currentServiceObjectiveName),
    sku = tostring(sku.name)
```

### Finding Template
**Title:** SQL Database using DTU-based purchasing model  
**What was found:** SQL Database `{name}` in resource group `{resourceGroup}` is using the DTU model with tier `{serviceTier}`.  
**Why it matters:** The DTU model bundles CPU, memory, and I/O into opaque units, making it difficult to right-size or troubleshoot performance bottlenecks independently. The vCore model offers granular control, zone redundancy options, and access to the Hyperscale tier.  
**Recommendation:** Evaluate migration to the vCore model (General Purpose or Business Critical). Use the DTU-to-vCore mapping guidance to select the equivalent vCore configuration, then test workload performance before switching.

### Learn More
- [vCore purchasing model for Azure SQL Database](https://learn.microsoft.com/azure/azure-sql/database/service-tiers-sql-database-vcore) — Features, resource limits, and pricing for vCore-based tiers
- [DTU resource limits for single databases](https://learn.microsoft.com/azure/azure-sql/database/resource-limits-dtu-single-databases) — DTU-based tier limits and feature comparison

---

## PERF-021 — SQL Database on lowest tier

**Pillar:** Performance  
**Severity:** Low  
**Profiles:** startup: Low, scale-up: Low, enterprise: Low

### What to Check
Query production SQL databases that are on the Basic (5 DTU) or Standard S0 (10 DTU) tier, which provide minimal compute capacity.

```kusto
resources
| where type == "microsoft.sql/servers/databases"
| where properties.currentServiceObjectiveName in~ ("Basic", "S0")
| where name != "master"
| where resourceGroup matches regex "(?i)(prod|prd|production)"
| project name, resourceGroup, subscriptionId,
    serviceTier = tostring(properties.currentServiceObjectiveName)
```

### Finding Template
**Title:** Production SQL Database on lowest tier  
**What was found:** SQL Database `{name}` in resource group `{resourceGroup}` is running on `{serviceTier}` tier, which provides only 5–10 DTUs of compute capacity.  
**Why it matters:** Basic and S0 tiers offer very limited throughput and can become a bottleneck under moderate load. At sustained utilization above 80%, queries slow down, timeouts increase, and application responsiveness degrades.  
**Recommendation:** Monitor DTU consumption in Azure Monitor. If average utilization exceeds 80%, scale up to a higher tier (S1 or above). Consider vCore model for more predictable performance scaling.

### Learn More
- [Monitor and tune Azure SQL Database](https://learn.microsoft.com/azure/azure-sql/database/monitor-tune-overview) — Performance monitoring tools and recommendations
- [Scale single database resources in Azure SQL Database](https://learn.microsoft.com/azure/azure-sql/database/scale-resources) — How to change service tier and compute size

---

## PERF-022 — Cosmos DB using provisioned throughput without autoscale

**Pillar:** Performance  
**Severity:** Medium  
**Profiles:** startup: Medium, scale-up: Medium, enterprise: Medium

### What to Check
Query Cosmos DB accounts and check whether containers use fixed provisioned throughput (manual RU/s) instead of autoscale. This requires checking the throughput settings via the Cosmos DB resource provider.

```kusto
resources
| where type =~ "microsoft.documentdb/databaseaccounts"
| project name, resourceGroup, subscriptionId,
    offerType = tostring(properties.databaseAccountOfferType)
```

For each account, use the Azure REST API or CLI to inspect container throughput settings:

```
az cosmosdb sql container throughput show \
  --account-name {name} \
  --database-name {db} \
  --name {container} \
  --resource-group {resourceGroup}
```

If `resource.autoscaleSettings` is absent and `resource.throughput` is a fixed value, this finding applies.

### Finding Template
**Title:** Cosmos DB container using fixed provisioned throughput  
**What was found:** Cosmos DB account `{name}` in resource group `{resourceGroup}` has containers with fixed provisioned RU/s and no autoscale enabled.  
**Why it matters:** Fixed provisioned throughput cannot adapt to traffic spikes. When request volume exceeds provisioned RU/s, Cosmos DB returns HTTP 429 (throttling) errors, causing application failures. Over-provisioning to avoid throttling wastes cost during low-traffic periods.  
**Recommendation:** Enable autoscale on containers with variable workload patterns. Autoscale adjusts RU/s between 10% and 100% of the configured maximum, balancing cost and performance automatically.

### Learn More
- [Provision autoscale throughput on Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/provision-throughput-autoscale) — How to configure and manage autoscale throughput
- [How to choose between standard and autoscale provisioned throughput](https://learn.microsoft.com/azure/cosmos-db/how-to-choose-offer) — Decision guide for selecting the right throughput model

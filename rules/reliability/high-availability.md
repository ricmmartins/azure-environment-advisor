# Reliability Assessment Rules — High Availability

Rules for assessing whether Azure compute and networking resources are configured for high availability through autoscaling, health monitoring, and redundant instance deployments.

---

## REL-020 — No autoscale configured for compute

**Pillar:** Reliability
**Severity:** High
**Profiles:** enterprise: High · scale-up: High · startup: Medium

### What to Check
App Service Plans and Virtual Machine Scale Sets without autoscale settings configured.

```kusto
resources
| where type in ("microsoft.web/serverfarms", "microsoft.compute/virtualmachinescalesets")
| join kind=leftouter (
    resources
    | where type == "microsoft.insights/autoscalesettings"
    | extend targetId = tolower(tostring(properties.targetResourceUri))
    | project targetId, autoscaleEnabled=properties.enabled
) on $left.id == $right.targetId
| where isempty(targetId) or autoscaleEnabled == false
| project name, resourceGroup, location, type, currentInstances=coalesce(properties.numberOfWorkers, sku.capacity)
```

### Finding Template
**Title:** Compute resource has no autoscale configuration
**What was found:** `{type}` resource `{name}` in resource group `{resourceGroup}` has no autoscale settings configured. Current instance count: `{currentInstances}`.
**Why it matters:** Without autoscale, the resource cannot respond to traffic spikes or increased load, leading to degraded performance or outages during peak demand. Conversely, without scale-in rules, resources remain over-provisioned during low-traffic periods, wasting cost. Autoscale ensures the right capacity is available at the right time.
**Recommendation:** Configure autoscale rules based on CPU percentage, memory usage, or custom metrics. Set a minimum instance count that meets baseline load, a maximum that covers peak scenarios, and scale-out/scale-in thresholds with appropriate cooldown periods (minimum 5 minutes).

### Learn More
- [Overview of autoscale in Azure](https://learn.microsoft.com/azure/azure-monitor/autoscale/autoscale-overview) — Autoscale concepts, metrics, and configuration
- [Scale up an app in Azure App Service](https://learn.microsoft.com/azure/app-service/manage-scale-up) — Scaling App Service Plans vertically and horizontally

---

## REL-021 — Load balancer without health probes

**Pillar:** Reliability
**Severity:** High
**Profiles:** enterprise: High · scale-up: High · startup: High

### What to Check
Load Balancers or Application Gateways without properly configured health probes, or using default TCP probes instead of application-level HTTP probes.

```kusto
resources
| where type == "microsoft.network/loadbalancers"
| where isnull(properties.probes) or array_length(properties.probes) == 0
| project name, resourceGroup, location, sku=sku.name
```

```kusto
resources
| where type == "microsoft.network/applicationgateways"
| where isnull(properties.probes) or array_length(properties.probes) == 0
| project name, resourceGroup, location, sku=properties.sku.name
```

### Finding Template
**Title:** Load balancer has no health probes configured
**What was found:** `{type}` `{name}` in resource group `{resourceGroup}` has no health probes configured, or is using only default TCP probes without application-level health checks.
**Why it matters:** Without proper health probes, the load balancer cannot detect unhealthy backend instances. Traffic continues to be routed to failed or degraded instances, causing errors and timeouts for end users. TCP probes only verify port availability, not whether the application is actually functioning correctly.
**Recommendation:** Configure custom HTTP(S) health probes that target a dedicated `/health` endpoint on the application. The health endpoint should verify critical dependencies (database connectivity, cache availability). Set the probe interval to 15 seconds and the unhealthy threshold to 2 consecutive failures.

### Learn More
- [Load Balancer health probes](https://learn.microsoft.com/azure/load-balancer/load-balancer-custom-probe-overview) — Probe types, configuration, and best practices
- [Application Gateway health probes](https://learn.microsoft.com/azure/application-gateway/application-gateway-probe-overview) — Custom probe configuration for App Gateway

---

## REL-022 — Single instance VM (no availability)

**Pillar:** Reliability
**Severity:** High
**Profiles:** enterprise: High · scale-up: High · startup: Medium

### What to Check
Virtual machines not placed in an availability set, not deployed to an availability zone, and not part of a Virtual Machine Scale Set.

```kusto
resources
| where type == "microsoft.compute/virtualmachines"
| where isnull(properties.availabilitySet)
    and (isnull(zones) or array_length(zones) == 0)
    and isnull(properties.virtualMachineScaleSet)
| project name, resourceGroup, location, vmSize=properties.hardwareProfile.vmSize
```

### Finding Template
**Title:** VM is a single instance with no availability configuration
**What was found:** Virtual machine `{name}` (size: `{vmSize}`) in resource group `{resourceGroup}` is deployed as a single instance without any availability set, availability zone, or scale set membership.
**Why it matters:** Single-instance VMs have no redundancy. During planned maintenance events, the VM may be rebooted with downtime. During unplanned hardware failures, the VM becomes unavailable until Azure migrates it to healthy hardware. The SLA for a single-instance VM (99.9% with Premium SSD) is significantly lower than zone-redundant or multi-instance deployments (99.99%).
**Recommendation:** For production workloads, migrate to a Virtual Machine Scale Set with Flexible orchestration mode across availability zones. If VMSS is not feasible, deploy the VM into an availability zone for 99.99% SLA. At minimum, use an availability set with other VMs for fault domain isolation.

### Learn More
- [Availability options for Azure VMs](https://learn.microsoft.com/azure/virtual-machines/availability) — Comparison of availability sets, zones, and scale sets
- [Reliability in Azure Virtual Machines](https://learn.microsoft.com/azure/reliability/reliability-virtual-machines) — Best practices for VM high availability

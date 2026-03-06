# Reliability Assessment Rules — Disaster Recovery

Rules for assessing whether Azure workloads have appropriate disaster recovery strategies, documented recovery targets, and cross-region protection.

---

## REL-030 — No multi-region strategy

**Pillar:** Reliability
**Severity:** High
**Profiles:** enterprise: High · scale-up: Medium · startup: Medium

### What to Check
All resources deployed to a single Azure region with no cross-region routing (Traffic Manager / Azure Front Door) and no database geo-replication.

```kusto
resources
| where type !in ("microsoft.resources/subscriptions", "microsoft.resources/subscriptions/resourcegroups")
| summarize regionCount=dcount(location), regions=make_set(location), resourceCount=count() by subscriptionId
| where regionCount == 1
| project subscriptionId, regions, resourceCount
```

```kusto
resources
| where type in ("microsoft.network/trafficmanagerprofiles", "microsoft.cdn/profiles")
| project name, type, resourceGroup
```

### Finding Template
**Title:** All resources are deployed in a single Azure region
**What was found:** All `{resourceCount}` resources in subscription `{subscriptionId}` are deployed in region `{regions}` only. No Traffic Manager, Azure Front Door, or geo-replicated databases were detected.
**Why it matters:** A single-region deployment has no protection against a full regional outage. While rare, regional outages do occur and can last hours. Without a multi-region strategy, the entire workload becomes unavailable with no failover path. Recovery requires manual intervention and can take significant time.
**Recommendation:** Document RPO/RTO targets for each workload tier. For critical workloads, deploy active-passive or active-active across a secondary region using Azure Front Door or Traffic Manager for routing. Start with database geo-replication and Site Recovery for VMs, then expand to full multi-region deployment.

### Learn More
- [Azure reliability overview](https://learn.microsoft.com/azure/reliability/overview) — Reliability principles and multi-region design patterns
- [Business continuity and disaster recovery](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/design-area/management-business-continuity-disaster-recovery) — Cloud Adoption Framework DR guidance

---

## REL-031 — No documented RPO/RTO targets

**Pillar:** Reliability
**Severity:** Medium
**Profiles:** enterprise: Medium · scale-up: Medium · startup: Medium

### What to Check
This rule cannot be verified programmatically through Azure APIs or Resource Graph. It should always be raised as a recommendation during assessments to prompt a conversation about recovery objectives.

> **Note:** This is a process/governance check. Flag it as a recommendation in every assessment unless the customer confirms documented RPO/RTO targets exist.

### Finding Template
**Title:** RPO/RTO targets are not documented or validated
**What was found:** No evidence of documented Recovery Point Objective (RPO) and Recovery Time Objective (RTO) targets was found for workloads in this environment. This finding is flagged by default as it cannot be verified through automated scanning.
**Why it matters:** Without defined RPO and RTO targets, it is impossible to determine whether the current architecture meets business recovery requirements. Teams cannot make informed decisions about backup frequency, replication strategy, or failover architecture. During an actual disaster, undefined targets lead to ad-hoc decisions, confusion, and potentially unacceptable data loss or downtime.
**Recommendation:** Define RPO and RTO targets for each workload based on business impact analysis. Validate that the current architecture (backup frequency, replication lag, failover mechanisms) can actually meet these targets. Conduct periodic DR drills to verify recovery within target timeframes. Document targets alongside the architecture and review them quarterly.

### Learn More
- [Business metrics for reliability](https://learn.microsoft.com/azure/reliability/business-metrics) — Defining RPO, RTO, and MTTR for Azure workloads
- [Reliability metrics](https://learn.microsoft.com/azure/well-architected/reliability/metrics) — Well-Architected Framework guidance on reliability metrics

---

## REL-032 — Site Recovery not configured for VMs

**Pillar:** Reliability
**Severity:** High
**Profiles:** enterprise: High · scale-up: Medium · startup: Low

### What to Check
Virtual machines without Azure Site Recovery (ASR) replication to a secondary region.

```kusto
recoveryservicesresources
| where type == "microsoft.recoveryservices/vaults/replicationfabrics/replicationprotectioncontainers/replicationprotecteditems"
| extend vmId = tolower(properties.providerSpecificDetails.fabricObjectId)
| project vmId, replicationHealth=properties.replicationHealth, failoverHealth=properties.failoverHealth
```

```kusto
resources
| where type == "microsoft.compute/virtualmachines"
| join kind=leftouter (
    recoveryservicesresources
    | where type == "microsoft.recoveryservices/vaults/replicationfabrics/replicationprotectioncontainers/replicationprotecteditems"
    | extend vmId = tolower(properties.providerSpecificDetails.fabricObjectId)
    | project vmId
) on $left.id == $right.vmId
| where isempty(vmId)
| project name, resourceGroup, location, vmSize=properties.hardwareProfile.vmSize
```

### Finding Template
**Title:** VM does not have Site Recovery replication configured
**What was found:** Virtual machine `{name}` (size: `{vmSize}`) in resource group `{resourceGroup}` (`{location}`) does not have Azure Site Recovery replication configured to a secondary region.
**Why it matters:** Without Site Recovery, a regional outage requires rebuilding the VM from scratch in another region — a process that can take hours or days depending on complexity. ASR continuously replicates VM disks to the target region, enabling failover within minutes with near-zero data loss (RPO typically under 1 minute for most workloads).
**Recommendation:** Configure Azure Site Recovery for this VM to replicate to the paired Azure region. Set up recovery plans to orchestrate failover order for multi-tier applications. Conduct test failovers quarterly to validate recovery without impacting production. Ensure the target region has sufficient quota for the required VM sizes.

### Learn More
- [About Site Recovery](https://learn.microsoft.com/azure/site-recovery/site-recovery-overview) — ASR architecture, supported scenarios, and capabilities
- [Enable Azure-to-Azure replication](https://learn.microsoft.com/azure/site-recovery/azure-to-azure-tutorial-enable-replication) — Step-by-step tutorial for VM replication

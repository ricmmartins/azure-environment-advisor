# Reliability Assessment Rules — Backup & Recovery

Rules for assessing whether Azure resources have appropriate backup policies, retention configurations, and recovery capabilities.

---

## REL-010 — No backup policy for Azure VMs

**Pillar:** Reliability
**Severity:** Critical
**Profiles:** enterprise: Critical · scale-up: Critical · startup: Critical

### What to Check
Virtual machines without Azure Backup protection — no association with a Recovery Services vault.

```kusto
resources
| where type == "microsoft.compute/virtualmachines"
| join kind=leftouter (
    recoveryservicesresources
    | where type == "microsoft.recoveryservices/vaults/backupfabrics/protectioncontainers/protecteditems"
    | where properties.backupManagementType == "AzureIaasVM"
    | extend vmId = tolower(properties.sourceResourceId)
    | project vmId
) on $left.id == $right.vmId
| where isempty(vmId)
| project name, resourceGroup, location, osType=properties.storageProfile.osDisk.osType
```

### Finding Template
**Title:** Azure VM has no backup policy configured
**What was found:** Virtual machine `{name}` (`{osType}`) in resource group `{resourceGroup}` is not protected by Azure Backup. No Recovery Services vault association was found.
**Why it matters:** Without backup protection, any data loss event — accidental deletion, ransomware, corruption, or disk failure — results in permanent, irrecoverable data loss. VMs often contain application state, configurations, and data that cannot be recreated.
**Recommendation:** Enable Azure Backup for this VM immediately. Configure a backup policy with daily backups and a minimum 30-day retention period. Use the Enhanced policy for multi-disk crash-consistent backups and support for up to 4 TB disks.

### Learn More
- [About Azure VM backup](https://learn.microsoft.com/azure/backup/backup-azure-vms-introduction) — Overview of VM backup architecture and capabilities
- [Back up a VM from the Azure portal](https://learn.microsoft.com/azure/backup/quick-backup-vm-portal) — Step-by-step quickstart guide

---

## REL-011 — SQL Database no long-term retention

**Pillar:** Reliability
**Severity:** Medium
**Profiles:** enterprise: Medium · scale-up: Medium · startup: Medium

### What to Check
SQL databases without a long-term retention (LTR) policy configured. The default short-term retention (PITR) covers only 7–35 days.

```kusto
resources
| where type == "microsoft.sql/servers/databases"
| where properties.currentSku.tier != "System"
| project name, resourceGroup, location, tier=properties.currentSku.tier
```

> **Note:** LTR policy configuration must be verified via the Azure SQL REST API (`GET /providers/Microsoft.Sql/servers/{server}/databases/{db}/backupLongTermRetentionPolicies/default`) as it is not available in Resource Graph.

### Finding Template
**Title:** SQL Database has no long-term backup retention configured
**What was found:** SQL database `{name}` in resource group `{resourceGroup}` does not have a long-term retention (LTR) policy. Only default short-term point-in-time restore (PITR) is active, covering up to 35 days.
**Why it matters:** Without LTR, backups older than the PITR window are permanently deleted. Compliance requirements, audit obligations, and disaster recovery scenarios often require retaining backups for months or years. If data corruption goes undetected beyond the PITR window, recovery becomes impossible.
**Recommendation:** Configure a long-term retention policy with weekly, monthly, and yearly backup retention. A common baseline: weekly backups retained 4 weeks, monthly retained 12 months, yearly retained 5 years. Adjust based on compliance and business requirements.

### Learn More
- [Long-term retention overview](https://learn.microsoft.com/azure/azure-sql/database/long-term-retention-overview) — How LTR works and retention policy options
- [Configure long-term backup retention](https://learn.microsoft.com/azure/azure-sql/database/long-term-backup-retention-configure) — Step-by-step configuration guide

---

## REL-012 — No geo-replication for critical databases

**Pillar:** Reliability
**Severity:** High
**Profiles:** enterprise: High · scale-up: Medium · startup: Low

### What to Check
Production SQL databases without active geo-replication or auto-failover group membership.

```kusto
resources
| where type == "microsoft.sql/servers/databases"
| where properties.currentSku.tier != "System"
| join kind=leftouter (
    resources
    | where type == "microsoft.sql/servers/failovergroups"
    | mv-expand db = properties.databases
    | extend dbId = tolower(tostring(db))
    | project dbId
) on $left.id == $right.dbId
| where isempty(dbId)
| project name, resourceGroup, location, tier=properties.currentSku.tier
```

### Finding Template
**Title:** SQL Database has no geo-replication or failover group
**What was found:** SQL database `{name}` in resource group `{resourceGroup}` (tier: `{tier}`) has no active geo-replication configured and is not a member of an auto-failover group.
**Why it matters:** Without geo-replication, a regional outage renders the database completely inaccessible until the region recovers. Active geo-replication provides an RPO of less than 5 seconds and enables rapid failover to a secondary region. Auto-failover groups additionally provide automatic failover and a single connection endpoint.
**Recommendation:** Configure an auto-failover group for this database with a secondary in the paired Azure region. Auto-failover groups provide an RPO < 5 seconds and automatic failover with grace period. Use the read-write listener endpoint for transparent connection redirection.

### Learn More
- [Auto-failover groups overview](https://learn.microsoft.com/azure/azure-sql/database/auto-failover-group-overview) — Automatic failover group concepts and configuration
- [Active geo-replication overview](https://learn.microsoft.com/azure/azure-sql/database/active-geo-replication-overview) — Manual geo-replication for fine-grained control

---

## REL-013 — Blob soft delete not enabled

**Pillar:** Reliability
**Severity:** Medium
**Profiles:** enterprise: Medium · scale-up: Medium · startup: Medium

### What to Check
Storage accounts without blob soft delete enabled, leaving blobs vulnerable to accidental or malicious deletion.

```kusto
resources
| where type == "microsoft.storage/storageaccounts"
| where isnull(properties.deleteRetentionPolicy) or properties.deleteRetentionPolicy.enabled == false
| project name, resourceGroup, location, kind=kind
```

> **Note:** Blob soft delete settings may need verification via the Storage Account REST API (`GET /providers/Microsoft.Storage/storageAccounts/{account}/blobServices/default`) as Resource Graph availability varies.

### Finding Template
**Title:** Blob soft delete is not enabled on storage account
**What was found:** Storage account `{name}` in resource group `{resourceGroup}` does not have blob soft delete enabled. Deleted blobs are permanently removed immediately.
**Why it matters:** Without soft delete, accidentally or maliciously deleted blobs cannot be recovered. This includes scenarios like application bugs overwriting data, accidental bulk deletions, or ransomware attacks. Soft delete provides a safety net by retaining deleted data for a configurable period.
**Recommendation:** Enable blob soft delete with a minimum 7-day retention period. For production workloads, consider 14–30 days. Also enable container soft delete and versioning for comprehensive data protection. These features have minimal cost impact relative to the protection they provide.

### Learn More
- [Soft delete for blobs overview](https://learn.microsoft.com/azure/storage/blobs/soft-delete-blob-overview) — How blob soft delete works and retention options
- [Enable soft delete for blobs](https://learn.microsoft.com/azure/storage/blobs/soft-delete-blob-enable) — Configuration via portal, CLI, and PowerShell

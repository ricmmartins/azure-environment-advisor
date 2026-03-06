# Operations Assessment Rules — Monitoring

Rules for assessing whether Azure monitoring infrastructure is properly configured to provide visibility into environment health and activity.

---

## OPS-001 — No diagnostic settings configured

**Pillar:** Operational Excellence  
**Severity:** Critical  
**Profiles:** startup: High · scale-up: Critical · enterprise: Critical

### What to Check
Query Azure Resource Graph for subscription-level diagnostic settings that forward the Activity Log to a Log Analytics workspace, Storage Account, or Event Hub. If none exist, the subscription has no centralized audit trail.

```kusto
resources
| where type == "microsoft.insights/diagnosticsettings"
| where isnotempty(properties.workspaceId) or isnotempty(properties.storageAccountId)
| summarize count()
```

Also check via Azure CLI:
```bash
az monitor diagnostic-settings subscription list --subscription {subscriptionId}
```

### Finding Template
**Title:** No diagnostic settings configured for Activity Log  
**What was found:** Subscription `{subscriptionName}` has no diagnostic settings forwarding the Activity Log to a central destination. Activity Log data is only retained for 90 days in-platform and is not available for advanced querying or long-term retention.  
**Why it matters:** The Activity Log records all control-plane operations — who created, modified, or deleted resources, and when. Without diagnostic settings, this critical audit trail is limited to 90-day in-portal retention with no ability to correlate with other signals, create alerts, or meet compliance requirements.  
**Recommendation:** Deploy a Log Analytics workspace and configure subscription-level diagnostic settings to forward all 8 Activity Log categories: Administrative, Security, ServiceHealth, Alert, Recommendation, Policy, Autoscale, and ResourceHealth.

### Learn More
- [Azure Activity Log](https://learn.microsoft.com/azure/azure-monitor/essentials/activity-log) — what the Activity Log captures and how to access it
- [Diagnostic settings in Azure Monitor](https://learn.microsoft.com/azure/azure-monitor/essentials/diagnostic-settings) — how to configure log forwarding to Log Analytics, Storage, or Event Hubs

---

## OPS-002 — No Log Analytics workspace

**Pillar:** Operational Excellence  
**Severity:** Critical  
**Profiles:** startup: High · scale-up: Critical · enterprise: Critical

### What to Check
Query Azure Resource Graph for `microsoft.operationalinsights/workspaces` resources. If none exist, there is no central destination for logs and metrics.

```kusto
resources
| where type == "microsoft.operationalinsights/workspaces"
| project name, resourceGroup, location,
    retentionDays = tostring(properties.retentionInDays),
    sku = tostring(properties.sku.name)
```

### Finding Template
**Title:** No Log Analytics workspace deployed  
**What was found:** Subscription `{subscriptionName}` has no Log Analytics workspace. There is no central destination for collecting logs, metrics, or diagnostic data from Azure resources.  
**Why it matters:** A Log Analytics workspace is the foundation of Azure monitoring. Without one, you cannot use Azure Monitor effectively, cannot run log queries for troubleshooting, and cannot enable Microsoft Defender for Cloud, Microsoft Sentinel, or VM Insights. This is the single most impactful monitoring gap.  
**Recommendation:** Deploy a central Log Analytics workspace in the same region as your primary workloads. Use the Per-GB pricing tier for most scenarios. Configure all diagnostic settings and VM agents to send data to this workspace.

### Learn More
- [Log Analytics workspace overview](https://learn.microsoft.com/azure/azure-monitor/logs/log-analytics-workspace-overview) — architecture, data ingestion, and retention options
- [Create a Log Analytics workspace](https://learn.microsoft.com/azure/azure-monitor/logs/quick-create-workspace) — quickstart guide for deploying a workspace

---

## OPS-003 — Resources missing diagnostic settings

**Pillar:** Operational Excellence  
**Severity:** Medium  
**Profiles:** startup: Low · scale-up: Medium · enterprise: High

### What to Check
Identify key resource types (SQL databases, App Services, Key Vaults, NSGs, Application Gateways) that do not have diagnostic settings configured. These resources generate important logs that are lost without explicit forwarding.

```kusto
resources
| where type in (
    "microsoft.sql/servers/databases",
    "microsoft.web/sites",
    "microsoft.keyvault/vaults",
    "microsoft.network/networksecuritygroups",
    "microsoft.network/applicationgateways")
| join kind=leftouter (
    resources
    | where type == "microsoft.insights/diagnosticsettings"
    | extend resourceId = tostring(properties.resourceId)
) on $left.id == $right.resourceId
| where isempty(resourceId)
| project name, type, resourceGroup, location
```

### Finding Template
**Title:** Critical resources missing diagnostic settings  
**What was found:** Found {count} resource(s) of key types without diagnostic settings in subscription `{subscriptionName}`. Resource types affected: {typeList}. These resources are not forwarding logs or metrics to any central destination.  
**Why it matters:** Without diagnostic settings on critical resources, you lose visibility into SQL query performance, App Service request logs, Key Vault access audit trails, and NSG flow logs. This creates blind spots for troubleshooting, security investigation, and compliance.  
**Recommendation:** Enable diagnostic settings on all critical resources, forwarding logs and metrics to the central Log Analytics workspace. Prioritize Key Vault (audit logs), NSGs (flow logs), SQL databases (query performance), and App Services (HTTP logs and errors).

### Learn More
- [Diagnostic settings in Azure Monitor](https://learn.microsoft.com/azure/azure-monitor/essentials/diagnostic-settings) — how to configure per-resource diagnostic settings for logs and metrics

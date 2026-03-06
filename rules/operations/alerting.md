# Operations Assessment Rules — Alerting

Rules for assessing whether Azure alerting is configured to proactively notify teams of issues before they impact users.

---

## OPS-030 — No alert rules configured

**Pillar:** Operational Excellence  
**Severity:** High  
**Profiles:** startup: Medium · scale-up: High · enterprise: High

### What to Check
Query Azure Resource Graph for metric alert rules and scheduled query rules. If none exist, the environment has no proactive alerting.

```kusto
resources
| where type in (
    "microsoft.insights/metricalerts",
    "microsoft.insights/scheduledqueryrules")
| summarize count() by type
```

### Finding Template
**Title:** No alert rules configured  
**What was found:** Subscription `{subscriptionName}` has no metric alerts or scheduled query rules configured. There is no automated notification for CPU spikes, memory pressure, HTTP errors, failed logins, or any other operational signal.  
**Why it matters:** Without alerting, issues are only discovered when users report them — often after significant impact has already occurred. Proactive alerting enables teams to respond to problems within minutes instead of hours or days, reducing mean time to recovery (MTTR) and minimizing business impact.  
**Recommendation:** Create metric alert rules for critical thresholds: CPU utilization > 85%, memory utilization > 85%, disk space > 90%, HTTP 5xx error rate spikes, and failed authentication attempts. Start with the most critical production resources and expand coverage over time.

### Learn More
- [Azure Monitor alerts overview](https://learn.microsoft.com/azure/azure-monitor/alerts/alerts-overview) — types of alerts, how they work, and best practices
- [Create a metric alert rule](https://learn.microsoft.com/azure/azure-monitor/alerts/alerts-create-metric-alert-rule) — step-by-step guide to creating metric-based alerts

---

## OPS-031 — No action groups configured

**Pillar:** Operational Excellence  
**Severity:** High  
**Profiles:** startup: Medium · scale-up: High · enterprise: High

### What to Check
Query Azure Resource Graph for action groups. If none exist, even if alert rules were configured, notifications would have no destination.

```kusto
resources
| where type == "microsoft.insights/actiongroups"
| project name, resourceGroup, location,
    emailReceivers = array_length(properties.emailReceivers),
    smsReceivers = array_length(properties.smsReceivers),
    webhookReceivers = array_length(properties.webhookReceivers)
```

### Finding Template
**Title:** No action groups configured  
**What was found:** Subscription `{subscriptionName}` has no action groups defined. Without action groups, alert rules have no notification targets — alerts fire but nobody is notified.  
**Why it matters:** Action groups are the delivery mechanism for alert notifications. Without them, even well-configured alert rules are silent — the system detects problems but cannot notify anyone. This creates a false sense of security where teams believe monitoring is in place but alerts are effectively useless.  
**Recommendation:** Create at least one action group with email and SMS notification channels for the on-call engineering team. For mature organizations, add webhook receivers to integrate with incident management tools (PagerDuty, Opsgenie, ServiceNow). Create separate action groups for different severity levels.

### Learn More
- [Action groups](https://learn.microsoft.com/azure/azure-monitor/alerts/action-groups) — how to create and configure action groups with various notification channels
- [Create action groups with Resource Manager templates](https://learn.microsoft.com/azure/azure-monitor/alerts/action-groups-create-resource-manager-template) — deploy action groups as code using ARM/Bicep templates

---

## OPS-032 — No Service Health alerts

**Pillar:** Operational Excellence  
**Severity:** Medium  
**Profiles:** startup: Low · scale-up: Medium · enterprise: High

### What to Check
Query Azure Resource Graph for activity log alerts that monitor the ServiceHealth category. These alerts notify when Azure platform issues, planned maintenance, or health advisories affect your resources.

```kusto
resources
| where type == "microsoft.insights/activitylogalerts"
| where tostring(properties.condition) contains "ServiceHealth"
| project name, resourceGroup,
    enabled = tostring(properties.enabled),
    scopes = tostring(properties.scopes)
```

### Finding Template
**Title:** No Service Health alerts configured  
**What was found:** Subscription `{subscriptionName}` has no Service Health alerts. The team will not be automatically notified when Azure platform incidents, planned maintenance, or health advisories affect their deployed resources.  
**Why it matters:** Azure platform issues can impact your workloads without any change on your side. Without Service Health alerts, teams may spend hours troubleshooting application issues that are actually caused by an Azure service incident. Service Health alerts provide early warning and context that dramatically reduces diagnosis time.  
**Recommendation:** Create Service Health alerts for all three notification types: service incidents (outages), planned maintenance (upcoming changes), and health advisories (action required). Scope the alerts to the regions and services where your resources are deployed, and route them to your primary action group.

### Learn More
- [Create Service Health alerts](https://learn.microsoft.com/azure/service-health/alerts-activity-log-service-notifications-portal) — step-by-step guide to configuring Service Health alert rules
- [Azure Service Health overview](https://learn.microsoft.com/azure/service-health/overview) — how Service Health tracks platform issues and communicates with customers

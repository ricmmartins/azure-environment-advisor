# Cost Assessment Rules — Budget Alerts

Rules for assessing whether budget alerts and cost anomaly detection are configured to prevent unexpected Azure spend.

---

## COST-001 — No budget alerts configured

**Pillar:** Cost Optimization  
**Severity:** High  
**Profiles:** startup: Medium · scale-up: High · enterprise: High

### What to Check
Query Azure Resource Graph for `microsoft.consumption/budgets` resources on the subscription. If none exist, the subscription has no spend guardrails.

```kusto
resources
| where type == "microsoft.consumption/budgets"
| summarize count()
```

### Finding Template
**Title:** No budget alerts configured  
**What was found:** Subscription `{subscriptionName}` has no Azure budgets defined. There are no automated alerts to notify when spending approaches or exceeds expected levels.  
**Why it matters:** Without budget alerts, cost overruns can go unnoticed for days or weeks, leading to unexpected bills. A single misconfigured autoscale or runaway workload can result in thousands of dollars in unplanned spend.  
**Recommendation:** Create a monthly budget in Azure Cost Management with alert thresholds at 50%, 80%, and 100% of actual spend, plus a 100% forecasted spend alert. Assign an action group that notifies the finance and engineering teams via email.

### Learn More
- [Tutorial: Create and manage budgets](https://learn.microsoft.com/azure/cost-management-billing/costs/tutorial-acm-create-budgets) — step-by-step guide to creating budget alerts in the Azure portal
- [Analyze unexpected charges](https://learn.microsoft.com/azure/cost-management-billing/understand/analyze-unexpected-charges) — techniques for investigating and preventing surprise bills

---

## COST-002 — No cost anomaly detection

**Pillar:** Cost Optimization  
**Severity:** Medium  
**Profiles:** startup: Low · scale-up: Medium · enterprise: Medium

### What to Check
Verify whether cost anomaly alerts are configured in Azure Cost Management. Check for anomaly alert rules via the Cost Management API or portal. Anomaly detection uses machine learning to identify unusual spending patterns.

### Finding Template
**Title:** No cost anomaly detection configured  
**What was found:** Subscription `{subscriptionName}` does not have cost anomaly detection alerts enabled. Unusual spending patterns will not trigger automatic notifications.  
**Why it matters:** Cost anomalies — such as a spike from a crypto-mining attack, a misconfigured resource, or an unexpected scale event — can accumulate significant charges before anyone notices. Anomaly detection catches these patterns early using machine learning.  
**Recommendation:** Enable cost anomaly detection in Azure Cost Management. Configure anomaly alerts to notify the appropriate team when spending deviates significantly from historical patterns.

### Learn More
- [Analyze unexpected charges](https://learn.microsoft.com/azure/cost-management-billing/understand/analyze-unexpected-charges) — how to use Cost Management tools including anomaly detection to investigate cost spikes

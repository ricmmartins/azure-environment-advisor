# Cost Assessment Rules — Reservations & Savings Plans

Rules for assessing whether long-running Azure workloads are covered by reserved instances or savings plans to reduce compute costs.

---

## COST-030 — No reserved instances for steady-state workloads

**Pillar:** Cost Optimization  
**Severity:** Medium (scale-up/enterprise), Low (startup)  
**Profiles:** startup: Low · scale-up: Medium · enterprise: Medium

### What to Check
Identify VMs that have been running continuously (24/7) for 30+ days without reserved instance or savings plan coverage. Cross-reference with Azure Advisor reservation purchase recommendations.

```kusto
advisorresources
| where type == "microsoft.advisor/recommendations"
| where tostring(properties.category) == "Cost"
| where tostring(properties.shortDescription.solution) contains "reserved"
    or tostring(properties.shortDescription.solution) contains "reservation"
| project name, resourceGroup,
    annualSavings = tostring(properties.extendedProperties.annualSavingsAmount),
    lookbackPeriod = tostring(properties.extendedProperties.lookbackPeriod),
    recommendedSku = tostring(properties.extendedProperties.displaySKU),
    term = tostring(properties.extendedProperties.term)
```

### Finding Template
**Title:** No reserved instances for steady-state workloads  
**What was found:** Found {count} VM(s) running 24/7 in subscription `{subscriptionName}` without reserved instance or savings plan coverage. Estimated annual savings with reservations: ~${totalSavings}.  
**Why it matters:** Pay-as-you-go pricing for always-on VMs is the most expensive option. Reserved instances offer 40% savings (1-year term) or up to 60% savings (3-year term) for committed usage, representing significant budget that could be redirected to other priorities.  
**Recommendation:** Purchase 1-year reserved instances for workloads with a stable 12-month outlook, or 3-year reservations for core infrastructure. Start with the Azure Advisor reservation recommendations which analyze your actual usage patterns.

### Learn More
- [Save costs with Azure Reserved VM Instances](https://learn.microsoft.com/azure/cost-management-billing/reservations/save-compute-costs-reservations) — how reservations work, purchasing options, and management
- [Azure Savings Plan for compute](https://learn.microsoft.com/azure/cost-management-billing/savings-plan/savings-plan-compute-overview) — flexible alternative to reservations that applies across VM families and regions

---

## COST-031 — No savings plan coverage

**Pillar:** Cost Optimization  
**Severity:** Low  
**Profiles:** startup: Low · scale-up: Low · enterprise: Medium

### What to Check
Review overall compute spend and check whether any Azure Savings Plans are active on the enrollment or subscription. Savings plans offer flexibility over reservations by applying discounts across VM families and regions.

### Finding Template
**Title:** No savings plan coverage for compute spend  
**What was found:** Subscription `{subscriptionName}` has compute spend of ~${monthlySpend}/month with no Azure Savings Plan coverage. No active savings plans were detected at the subscription or enrollment level.  
**Why it matters:** Azure Savings Plans provide automatic discounts (up to 65% off pay-as-you-go) across compute services without locking into specific VM sizes or regions. For organizations with dynamic workloads that shift between VM families, savings plans offer better flexibility than reserved instances.  
**Recommendation:** Evaluate Azure Savings Plan for compute if your workloads shift across VM families or regions. Use the savings plan recommendation tool in Azure Cost Management to model potential savings based on your historical usage.

### Learn More
- [Azure Savings Plan for compute](https://learn.microsoft.com/azure/cost-management-billing/savings-plan/savings-plan-compute-overview) — overview of how savings plans work, eligibility, and purchasing options

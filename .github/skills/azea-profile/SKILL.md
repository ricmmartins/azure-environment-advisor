---
name: azea-profile
description: Determine the environment profile (startup, scale-up, or enterprise) based on discovery data signals, then load the matching profile to calibrate severity levels and recommendation tone.
license: MIT
metadata:
  author: Azure Environment Advisor
  version: "1.0"
  project: AzureEnvironmentAdvisor
---

Analyze discovery data to determine whether the environment is a startup, scale-up, or enterprise — then load the matching profile to calibrate the assessment.

**Input**: Discovery data from `azea-discover` (preferred), or a subscription ID to self-discover if run standalone.

**Tools required**: Azure MCP Server (for standalone mode), File system tools (to read profile definitions)

**Reference files**:
- `.github/skills/shared/profile-detection.md` — Signal thresholds and matching algorithm
- `profiles/startup.md` — Startup profile definition and severity adjustments
- `profiles/scaleup.md` — Scale-up profile definition and severity adjustments
- `profiles/enterprise.md` — Enterprise profile definition and severity adjustments

**Shared procedures** (MUST follow):
- `.github/skills/shared/procedures/azure-authentication.md` — Azure session check (only if running standalone)

---

## Steps

### 1. Obtain Discovery Data

#### 1a. If discovery data is available (from a prior azea-discover run)
Use the existing discovery data directly. Skip to Step 2.

#### 1b. If running standalone (no prior discovery)
Follow `.github/skills/shared/procedures/azure-authentication.md`. **HARD GATE** — stop if not authenticated.

Run the minimal queries needed for profiling:
```kql
resourcecontainers | where type == 'microsoft.resources/subscriptions' | summarize count()
```
```kql
resourcecontainers | where type == 'microsoft.management/managementgroups' | where name != tenantId | summarize count()
```
```kql
resources | summarize totalResources=count(), regions=dcount(location), resourceGroups=dcount(resourceGroup)
```
```kql
resources | where type == 'microsoft.network/azurefirewalls' | summarize count()
```
```kql
resources | where type == 'microsoft.network/virtualnetworks' | where name contains 'hub' or name contains 'connectivity' or name contains 'transit' | summarize count()
```
```kql
policyresources | where type == 'microsoft.authorization/policyassignments' | summarize count()
```

### 2. Compute Profile Signals

Using the signal thresholds from `.github/skills/shared/profile-detection.md`, compute each of the 7 signals:

| # | Signal | Value | Startup Match | Scale-up Match | Enterprise Match |
|---|--------|-------|---------------|----------------|------------------|
| 1 | Subscriptions | ? | ? | ? | ? |
| 2 | Management Groups | ? | ? | ? | ? |
| 3 | Total Resources | ? | ? | ? | ? |
| 4 | Regions | ? | ? | ? | ? |
| 5 | Hub VNet / Firewall | ? | ? | ? | ? |
| 6 | Resource Groups | ? | ? | ? | ? |
| 7 | Policy Assignments | ? | ? | ? | ? |

### 3. Apply Matching Algorithm

Follow the matching algorithm from `.github/skills/shared/profile-detection.md`:

1. Count matching signals per profile
2. If one profile leads with ≥3 signals → use it
3. If tied → pick lower maturity (Startup < Scale-up < Enterprise)
4. If evenly split → default to Scale-up
5. If fewer than 3 match any → default to Startup

### 4. Load Profile Definition

Read the matching profile file from `profiles/`:
- `profiles/startup.md` for Startup
- `profiles/scaleup.md` for Scale-up
- `profiles/enterprise.md` for Enterprise

Extract:
- **Philosophy** — how to frame recommendations
- **What matters most** — priority areas
- **Expectations** — what's reasonable at this stage
- **Severity Adjustments table** — rule ID → profile-specific severity overrides

### 5. Present Profile Result

```
## Environment Profile: <Profile Name>

**Signal breakdown:**

| Signal | Value | Matched Profile |
|--------|-------|-----------------|
| Subscriptions | N | <profile> |
| Management Groups | N | <profile> |
| Total Resources | N | <profile> |
| ... | ... | ... |

**Result**: N/7 signals match <selected profile> (next closest: <runner-up> with N/7)

**What this means:**
<Philosophy excerpt from the profile file>

**Severity adjustments active**: N rules have adjusted severity for this profile.

**Next step**: Run `/azea-assess` to evaluate your environment against best practices, or `/azea-full-assessment` for the complete assessment.
```

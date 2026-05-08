---
name: azea-remediate
description: Remediate assessment findings by deploying ARM templates via the ARM MCP Server. Supports dry-run preview, explicit user confirmation, deployment monitoring, and rollback. Opt-in only — never auto-deploys.
license: MIT
metadata:
  author: Azure Environment Advisor
  version: "1.0"
  project: AzureEnvironmentAdvisor
---

Remediate assessment findings by deploying ARM templates through the Azure Resource Manager MCP Server. Every deployment requires explicit user confirmation.

**Input**: Assessment findings from `azea-assess`, or specific finding IDs to remediate.

**Tools required**: ARM MCP Server (deployment tools), Azure MCP Server (resource validation), Terminal (for `az` CLI fallback)

**Reference files**:
- `.github/skills/shared/assessment-model.md` — Finding data model (includes remediation schema)
- `.github/skills/shared/procedures/arm-mcp-server.md` — ARM MCP Server tool reference
- `.github/skills/shared/procedures/azure-authentication.md` — Azure session check

---

## ⚠️ Safety Notice

This is the **only skill** in Azure Environment Advisor that can **modify Azure resources**. All other skills operate in read-only mode. This skill:

- **Requires explicit user confirmation** for every deployment
- **Shows a preview** of what will be deployed before execution
- **Never auto-deploys** — not even when chained from `azea-full-assessment`
- **Only performs additive/update operations** — never deletes resources
- **Targets existing resource groups only** — never creates new resource groups
- **Requires Contributor role** on the target resource group (Reader is not sufficient)

---

## Steps

### 1. Check Azure Authentication

Follow `.github/skills/shared/procedures/azure-authentication.md`. **HARD GATE** — stop if not authenticated.

### 2. Verify Permissions

Check that the user has **Contributor** role (or higher) on the target resource group(s):

```bash
az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv) \
  --scope /subscriptions/<sub-id>/resourceGroups/<rg-name> \
  --query "[].roleDefinitionName" -o tsv
```

If the user only has Reader access:
```
## Insufficient Permissions

Remediation requires **Contributor** role on the target resource group.
Your current role: Reader

Ask your Azure administrator to assign the Contributor role, or remediate manually
following the recommendations in the assessment report.
```

**HARD GATE** — stop if permissions are insufficient.

### 3. Select Findings to Remediate

#### 3a. From assessment findings (in-memory)

If assessment findings are available from a prior `azea-assess` run:
- List all findings with severity Critical and High
- Ask the user which findings to remediate

#### 3b. From specific finding IDs

If the user specifies finding IDs (e.g., "remediate SEC-001 and REL-003"):
- Look up those findings in the assessment data
- Confirm the findings and affected resources

#### 3c. From HTML report or baseline

If the user provides a report or baseline file:
- Parse the findings from the file
- Present the list and ask which to remediate

### 4. Generate Remediation Plan

For each selected finding:

1. **Determine remediability** — not all findings can be remediated via ARM templates. Classify:
   - ✅ **Remediable**: Resource configuration changes (enable private endpoints, enable Defender plans, configure diagnostic settings, set up backup policies, etc.)
   - ⚠️ **Partially remediable**: Requires both ARM deployment and manual steps (e.g., enable MFA requires Entra ID changes)
   - ❌ **Not remediable via ARM**: Organizational changes, process improvements, architecture redesigns

2. **For remediable findings**, prepare an ARM template:
   - Use best-practice templates for common remediations
   - Generate the template description for user review
   - Identify the target resource group

3. **Present the remediation plan**:

```
## Remediation Plan

| # | Finding | Action | Resource Group | Risk |
|---|---------|--------|----------------|------|
| 1 | SEC-001 — Public endpoint on SQL | Deploy Private Endpoint | rg-contoso-prod | Low |
| 2 | OPS-003 — No diagnostic settings | Enable diagnostic settings | rg-contoso-prod | Low |
| 3 | SEC-005 — Defender not enabled | Enable Defender plans | (subscription-level) | Low |

### Not remediable via ARM template:
- REL-002 — No multi-region strategy (requires architecture redesign)
- GOV-001 — No management group hierarchy (requires org-level planning)

**⚠️ Review each action carefully before confirming.**
Shall I proceed with the remediable findings? (You'll confirm each deployment individually)
```

### 5. Execute Remediations

For each confirmed finding, one at a time:

#### 5a. Preview

Show the ARM template summary:
```
## Deploying: SEC-001 — Enable Private Endpoint for sql-contoso-prod

**Resource Group**: rg-contoso-prod
**Deployment name**: remediate-SEC-001-2026-05-08
**Template**: Creates a Private Endpoint for Microsoft.Sql/servers/sql-contoso-prod
**Changes**:
  - Creates: privateEndpoint/pe-sql-contoso-prod
  - Modifies: sql-contoso-prod (sets publicNetworkAccess = Disabled)

⚠️ This will modify resources in your Azure subscription.
Proceed with this deployment? (yes/no)
```

#### 5b. Deploy

If user confirms:
1. Use `create_template_deployment` to start the deployment
2. Use `get_arm_template_deployment_status` to monitor progress
3. Report status updates every 30 seconds

#### 5c. Monitor

```
## Deployment Progress: SEC-001

⏳ Status: Running... (started 45 seconds ago)
   Resources provisioned: 1/2
   - ✅ privateEndpoint/pe-sql-contoso-prod — Succeeded
   - ⏳ sql-contoso-prod — Updating publicNetworkAccess...
```

#### 5d. Handle failures

If a deployment fails:
```
## Deployment Failed: SEC-001

❌ Error: InsufficientPermissions — The client does not have permission to perform action...

Options:
1. Retry the deployment
2. Cancel and move to the next finding
3. Stop all remediations

What would you like to do?
```

If the user wants to cancel a running deployment:
- Use `cancel_arm_template_deployment` to stop it
- Report the cancellation status

### 6. Present Results

```
## Remediation Complete

| # | Finding | Status | Deployment |
|---|---------|--------|------------|
| 1 | SEC-001 — Public endpoint on SQL | ✅ Deployed | remediate-SEC-001-2026-05-08 |
| 2 | OPS-003 — No diagnostic settings | ✅ Deployed | remediate-OPS-003-2026-05-08 |
| 3 | SEC-005 — Defender not enabled | ❌ Failed | remediate-SEC-005-2026-05-08 |

**Successfully remediated**: 2 of 3 findings
**Failed**: 1 (SEC-005 — insufficient permissions at subscription scope)

### Recommended Next Steps
- Re-run `/azea-assess` to verify the remediations resolved the findings
- Address SEC-005 manually: enable Defender plans in the Azure Portal
- Review non-remediable findings in the assessment report for manual action
```

---

## Important Guidelines

- **Never auto-deploy** — every deployment requires explicit "yes" from the user
- **One at a time** — deploy findings sequentially, not in parallel
- **Preview first** — always show what will be deployed before executing
- **No deletes** — never include resource deletions in ARM templates
- **Existing RGs only** — deploy to existing resource groups, never create new ones
- **Monitor actively** — track deployment status and report to user
- **Offer cancellation** — if anything looks wrong, offer to cancel immediately
- **Log everything** — record deployment names and statuses for audit trail
- **Template quality** — warn users that AI-generated templates should be reviewed; recommend providing their own templates for critical resources

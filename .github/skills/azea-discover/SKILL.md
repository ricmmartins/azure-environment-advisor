---
name: azea-discover
description: Connect to one or more Azure subscriptions and discover all deployed resources, configurations, networking, security posture, compliance, and identity settings using Azure Resource Graph queries and the Azure MCP Server.
license: MIT
metadata:
  author: Azure Environment Advisor
  version: "1.0"
  project: AzureEnvironmentAdvisor
---

Connect to Azure subscription(s) and build a complete inventory of the environment — resources, networking, security, compliance, RBAC, monitoring, and more.

**Input**: One or more Azure subscription IDs, subscription names, or a management group ID. If not provided, the skill will prompt.

**Tools required**: Azure MCP Server (Resource Graph queries, resource details), Terminal (for `az` CLI fallback)

**Reference files**:
- `.github/skills/shared/assessment-model.md` — Shared data model
- `queries/resource-graph/inventory.kql` — Resource inventory query
- `queries/resource-graph/networking.kql` — Networking topology query
- `queries/resource-graph/security.kql` — Security posture query
- `queries/resource-graph/compliance.kql` — Compliance and policy query
- `queries/resource-graph/rbac.kql` — Identity and access query
- `queries/log-analytics/sign-in-anomalies.kql` — Sign-in anomaly detection
- `queries/log-analytics/resource-changes.kql` — Resource change tracking
- `queries/log-analytics/security-events.kql` — Security event monitoring

**Shared procedures** (MUST follow):
- `.github/skills/shared/procedures/azure-authentication.md` — Azure session check procedure
- `.github/skills/shared/procedures/mcp-query-execution.md` — How to run KQL via MCP

---

## Steps

### 1. Check Azure Authentication

Follow the procedure in `.github/skills/shared/procedures/azure-authentication.md`. **HARD GATE** — stop if not authenticated.

### 2. Identify Target Scope

#### 2a. Subscription(s) specified

If the user provides one or more subscription IDs or names:
- Validate connectivity to each subscription via Azure MCP Server
- Confirm the subscription name(s) and ID(s) with the user

#### 2b. Management group specified

If the user provides a management group ID:
- Enumerate all subscriptions under it:
  ```kql
  resourcecontainers
  | where type == 'microsoft.resources/subscriptions'
  | project subscriptionId, name, properties.displayName
  ```
- Confirm the list with the user before proceeding

#### 2c. No scope specified

Ask the user which subscription to assess. Wait for input.

#### 2d. Multi-subscription mode

If multiple subscriptions are provided (comma-separated, a list, or "all"):
- Assess each one sequentially
- Generate separate discovery data per subscription

### 3. Run Resource Graph Queries

Follow `.github/skills/shared/procedures/mcp-query-execution.md` for each query. Execute in this order:

#### 3a. Resource Inventory
Read and execute `queries/resource-graph/inventory.kql` to get:
- Total resource count by type, location, and resource group
- Resource types deployed (VMs, App Services, SQL, Storage, etc.)
- Regions in use
- Resource groups and their naming patterns

#### 3b. Networking Topology
Read and execute `queries/resource-graph/networking.kql` to discover:
- Virtual Networks, subnets, and address spaces
- NSGs and their associations
- Public IP addresses and their assignments
- VNet peerings and hub/spoke patterns
- Route tables, Application Gateways, Load Balancers, Front Door
- Private Endpoints and Private DNS Zones
- Azure Firewall instances

#### 3c. Security Posture
Read and execute `queries/resource-graph/security.kql` to evaluate:
- Defender for Cloud plans (enabled/disabled)
- Secure Score (current vs max)
- Defender recommendations and severity
- Resources with public network access enabled
- Storage accounts with public blob access
- Key Vault usage and access policies vs RBAC

#### 3d. Compliance & Policy
Read and execute `queries/resource-graph/compliance.kql` to check:
- Azure Policy assignments
- Non-compliant resources and violated policies
- Initiative assignments (built-in vs custom)
- Tag coverage across resources

#### 3e. Identity & Access
Read and execute `queries/resource-graph/rbac.kql` to review:
- Role assignments by principal type (User, Group, ServicePrincipal)
- Direct user assignments vs group-based
- Owner/Contributor counts at subscription scope
- Managed identity usage across resources

### 4. Run Log Analytics Queries (Optional)

If the environment has a Log Analytics workspace (found in inventory):
- Execute `queries/log-analytics/sign-in-anomalies.kql`
- Execute `queries/log-analytics/resource-changes.kql`
- Execute `queries/log-analytics/security-events.kql`

If no workspace exists, skip — note the limitation:
> "Log Analytics queries skipped — no workspace found. Sign-in anomaly and security event analysis requires a configured Log Analytics workspace."

### 5. Additional Discovery

Use the Azure MCP Server to also check:
- **Diagnostic settings** — are resources sending logs to Log Analytics?
- **Budget resources** — are consumption budgets configured?
- **Backup vaults** — are backup policies protecting critical resources?
- **Autoscale settings** — are compute resources set to autoscale?
- **Alert rules** — what monitoring alerts exist?
- **Action groups** — who gets notified when alerts fire?

### 6. Present Discovery Summary

Display a concise summary:
```
## Discovery Complete

**Subscription**: <name> (<id>)
**Total resources**: N
**Resource groups**: N
**Regions**: region1, region2
**Resource types**: N unique types

Key findings from discovery:
- Networking: N VNets, N subnets, N public IPs, N private endpoints
- Security: Defender <enabled/disabled>, Secure Score N%
- Compliance: N policy assignments, N non-compliant resources
- Identity: N role assignments, N managed identities

**Next step**: Run `/azea-profile` to determine your environment profile, or `/azea-full-assessment` for the complete assessment.
```

### 7. Store Discovery Data

Retain all discovery results — they will be used by:
- `azea-profile` (to compute profile signals)
- `azea-assess` (to evaluate rules)

Do not discard any query results until the assessment is complete.

---

## Error Handling

- **Query fails/times out**: Note which query failed, continue with remaining queries
- **inventory.kql fails**: Notify the user — this is the foundational query. Suggest re-running or checking permissions
- **Empty subscription (0 resources)**: Report "No resources found" — note as a new/empty subscription
- **Permission issues**: If queries return unexpectedly empty results, suggest checking roles with `az role assignment list --assignee <user>`

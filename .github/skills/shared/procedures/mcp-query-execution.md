# MCP Query Execution

Canonical procedure for running KQL queries via the Azure MCP Server. Referenced by skills that query Azure Resource Graph or Log Analytics.

---

## Resource Graph Queries

To run a KQL query against Azure Resource Graph:

1. **Read** the `.kql` file content from the repository (e.g., `queries/resource-graph/inventory.kql`)
2. **Pass** the KQL string to the Azure MCP Server's Resource Graph query tool
3. The server accepts the KQL string and returns results as structured data

### Available Tables

| Table | Purpose | Example |
|-------|---------|---------|
| `resources` | All Azure resources | `resources \| summarize count() by type` |
| `resourcecontainers` | Subscriptions, resource groups, management groups | `resourcecontainers \| where type == 'microsoft.resources/subscriptions'` |
| `securityresources` | Defender for Cloud data | Secure score, recommendations, pricing tiers |
| `policyresources` | Azure Policy data | Compliance state, policy assignments |
| `authorizationresources` | RBAC data | Role assignments, role definitions |

### Resource Details

To read a resource's detailed configuration, request it from the Azure MCP Server by its **resource ID** (obtained from Resource Graph results).

## Log Analytics Queries

Log Analytics queries require a workspace. Before running:

1. Check if a Log Analytics workspace exists in the discovery data
2. If yes, run the query against that workspace using the Azure MCP Server
3. If no workspace exists, skip — note the limitation

### Query Files

| File | Purpose |
|------|---------|
| `queries/log-analytics/sign-in-anomalies.kql` | Unusual sign-in patterns, risky sign-ins |
| `queries/log-analytics/resource-changes.kql` | Recent resource modifications and who made them |
| `queries/log-analytics/security-events.kql` | Defender alerts, JIT access, Key Vault operations |

## Error Handling

- **If a query fails or times out**: Note which query failed, continue with remaining queries
- **If `inventory.kql` fails** (foundational query): Notify the user and suggest checking permissions
- **If results are unexpectedly empty**: User may lack permissions — suggest `az role assignment list --assignee <user>`

## MCP Server Capabilities

The Azure MCP Server exposes its tools automatically via the Model Context Protocol. You do **not** need to know specific function names — your MCP client (VS Code Copilot, GitHub CLI) discovers available tools at runtime.

> **Note:** The Azure MCP Server operates in **read-only mode**. It cannot create, modify, or delete any Azure resource.

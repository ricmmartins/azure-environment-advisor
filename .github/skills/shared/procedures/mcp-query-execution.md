# MCP Query Execution

Canonical procedure for running KQL queries via MCP servers. Referenced by skills that query Azure Resource Graph or Log Analytics.

---

## Preferred: ARM MCP Server Query Pipeline

When the ARM MCP Server is available, use its query tools for Azure Resource Graph queries. This pipeline provides query generation from natural language, validation before execution, and optimized result handling.

See `.github/skills/shared/procedures/arm-mcp-server.md` for full tool reference.

### Pipeline: Pre-written KQL (from `.kql` files or rule definitions)

1. **Read** the `.kql` file content from the repository (e.g., `queries/resource-graph/inventory.kql`)
2. **Validate** the KQL string using the ARM MCP Server's `validate_query` tool
3. **Execute** the validated query using the ARM MCP Server's `execute_query` tool
4. If validation fails, log the error and fall back to the Azure MCP Server (see below)

### Pipeline: Dynamic Query Generation (no pre-written KQL)

1. **Describe** what you need in natural language (e.g., "Find all VMs without managed disks")
2. **Generate** a KQL query using the ARM MCP Server's `generate_query` tool
3. **Validate** the generated query using `validate_query`
4. **Execute** the validated query using `execute_query`
5. If generation fails, note as a limitation — do not fabricate queries

### When to use dynamic generation

| Scenario | Use dynamic generation? |
|----------|------------------------|
| Pre-written `.kql` file exists | No — use the file directly |
| Rule has embedded KQL in "What to Check" | No — use the embedded query |
| Rule describes a check but has no KQL | **Yes** — generate from the rule description |
| User asks an ad-hoc question | **Yes** — generate from the user's question |
| Need to discover a resource type not covered by existing queries | **Yes** — generate a targeted query |

## Fallback: Azure MCP Server

If the ARM MCP Server is unavailable or a query fails through the ARM pipeline, fall back to the Azure MCP Server:

1. **Read** the `.kql` file content from the repository
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

Two MCP servers provide Azure access:

### Azure MCP Server (General Purpose)
The Azure MCP Server exposes tools for resource access, configurations, and Log Analytics. It operates in **read-only mode** and cannot create, modify, or delete resources.

### ARM MCP Server (Query Intelligence + Deployments)
The ARM MCP Server provides specialized tools for ARG query generation, validation, and execution, plus ARM template deployment capabilities. Query tools are read-only; deployment tools require explicit user opt-in.

See `.github/skills/shared/procedures/arm-mcp-server.md` for the full tool reference.

> **Note:** Both servers discover their tools automatically via the Model Context Protocol. Your MCP client (VS Code Copilot, GitHub CLI) discovers available tools at runtime.

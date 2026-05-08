# ARM MCP Server Tools

Reference for the Azure Resource Manager MCP Server tools. This is a remote MCP server (public preview) that provides AI agents with first-class access to Azure infrastructure operations through ARM.

---

## Overview

The ARM MCP Server complements the existing Azure MCP Server. While the Azure MCP Server provides general-purpose resource access, the ARM MCP Server adds specialized tools for **query intelligence** and **infrastructure deployment**.

| Server | Purpose | Mode |
|--------|---------|------|
| **Azure MCP Server** (`@azure/mcp`) | General resource access, configurations, Log Analytics | Read-only |
| **ARM MCP Server** (remote) | ARG query generation/validation/execution, ARM deployments | Read + Write (opt-in) |

## Available Tools

### Query Tools (Read-Only)

| Tool | Purpose | When to use |
|------|---------|-------------|
| `generate_query` | Generate Azure Resource Graph (ARG) queries from natural language descriptions | When you need a KQL query but don't have one pre-written, or when a rule describes what to check but lacks embedded KQL |
| `validate_query` | Validate an ARG query for syntax and semantic correctness before execution | Before executing any query — especially generated or user-provided queries — to catch errors early |
| `execute_query` | Execute a validated ARG query and return structured results | To run ARG queries with optimized performance and structured response handling |

### Deployment Tools (Write — Opt-In Only)

| Tool | Purpose | When to use |
|------|---------|-------------|
| `create_template_deployment` | Deploy an ARM template to a resource group scope | When remediating a finding by deploying infrastructure changes (requires explicit user confirmation) |
| `get_arm_template_deployment_status` | Check the status of an active ARM template deployment | To monitor deployment progress after `create_template_deployment` |
| `cancel_arm_template_deployment` | Cancel a running ARM template deployment | When a deployment needs to be stopped (user request, detected issue, timeout) |

## Query Pipeline

For Azure Resource Graph queries, prefer this pipeline over direct execution:

```
1. generate_query  →  Natural language → KQL
2. validate_query  →  Verify syntax/semantics
3. execute_query   →  Run and get results
```

### When to use the pipeline vs. pre-written queries

| Scenario | Approach |
|----------|----------|
| Pre-written `.kql` file exists in `queries/` | Skip `generate_query`, go straight to `validate_query` → `execute_query` |
| Rule has embedded KQL in "What to Check" | Skip `generate_query`, go straight to `validate_query` → `execute_query` |
| Rule describes what to check but has no KQL | Use full pipeline: `generate_query` → `validate_query` → `execute_query` |
| User asks an ad-hoc question about resources | Use full pipeline: `generate_query` → `validate_query` → `execute_query` |
| Query from `.kql` file fails validation | Log the error, attempt `generate_query` with the same intent as fallback |

## Deployment Safety Gates

The deployment tools (`create_template_deployment`, etc.) are **only used by the `azea-remediate` skill** and require:

1. **Explicit user confirmation** — never auto-deploy
2. **Dry-run preview** — show what will be deployed before executing
3. **Scope limitation** — deployments target existing resource groups only
4. **Rollback awareness** — monitor status and offer cancellation if issues arise
5. **No destructive operations** — only additive/update deployments, never delete resources

## Authentication & Permissions

- **Query tools**: Require **Reader** role (same as existing Azure MCP Server)
- **Deployment tools**: Require **Contributor** role on the target resource group
- Authentication flows through the same Azure credentials (`az login` / VS Code Azure session)

## Server Configuration

The ARM MCP Server is a **remote** server — no local installation needed. Configure it via VS Code:

1. Open `https://aka.ms/JoinAzMgmtMCP` (installs the server in VS Code)
2. Sign in with Azure credentials
3. Verify tools are enabled in Copilot Chat → Configure Tools

Or add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "azure-mcp-server": {
      "command": "npx",
      "args": ["-y", "@azure/mcp@latest", "server", "start"]
    },
    "arm-mcp-server": {
      "url": "https://aka.ms/JoinAzMgmtMCP"
    }
  }
}
```

## Error Handling

| Error | Action |
|-------|--------|
| `generate_query` fails | Fall back to pre-written `.kql` query or note as limitation |
| `validate_query` finds errors | Log the validation error, attempt to regenerate with `generate_query` |
| `execute_query` times out | Retry once, then fall back to Azure MCP Server direct query |
| Deployment fails | Show error to user, offer `cancel_arm_template_deployment` if still running |
| ARM MCP Server unavailable | Fall back to Azure MCP Server for queries; skip remediation |

## Relationship to Existing Skills

| Skill | How it uses ARM MCP Server |
|-------|---------------------------|
| `azea-discover` | `generate_query` for dynamic discovery, `validate_query` + `execute_query` for all ARG queries |
| `azea-assess` | `generate_query` for rules without embedded KQL |
| `azea-remediate` | All deployment tools for finding remediation |
| `azea-full-assessment` | Orchestrates the above; offers remediation as optional step |

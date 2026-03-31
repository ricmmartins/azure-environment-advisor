# Azure Environment Advisor

An AI-powered agent that connects to your Azure subscription, assesses your environment against best practices, and generates an interactive HTML report with findings and Microsoft Learn documentation links — tailored to your company's stage and architecture.

## Quick Start

```bash
az login                           # Sign in with Reader access on the target subscription
git clone https://github.com/ricmmartins/azure-environment-advisor.git
cd azure-environment-advisor
```

Then **pick one**:

| Method | Setup |
|--------|-------|
| **Quick setup script** | `bash scripts/setup.sh` — prompts for subscription ID, creates `.vscode/mcp.json` for you |
| **VS Code (manual)** | Create `.vscode/mcp.json` ([template below](#5-configure-mcp-server)), open in VS Code, switch Copilot Chat to **Agent mode**, type: **"Assess my Azure subscription"** |
| **Copilot CLI** | `gh copilot -p "Assess my Azure subscription using the rules in this project" --allow-all` (requires Node.js 24+) |

👉 [Full setup guide](#getting-started) · [Sample report](https://htmlpreview.github.io/?https://github.com/ricmmartins/azure-environment-advisor/blob/main/samples/sample-report.html) · [Example issues](https://github.com/ricmmartins/azure-environment-advisor/issues)

## The Problem

Teams deploying on Azure today face a fragmented landscape of advisory tools:

| Tool | Covers | Limitation |
|---|---|---|
| Azure Advisor | Cost, reliability, security, performance | Generic recommendations, no context about your stage or architecture |
| Defender for Cloud | Security posture (Secure Score) | Security-only, no reliability/cost/networking holistic view |
| WAF Assessment | Well-Architected review (all 5 pillars) | Manual questionnaire — self-reported, doesn't scan actual resources |
| Azure Resource Graph | Resource inventory queries | Raw data — no intelligence or recommendation layer |
| Cost Management | Spending analysis + budget alerts | Cost-only, no connection to architecture decisions |

**The gap:** No single tool connects to your actual environment, assesses it holistically across all Well-Architected pillars, contextualizes recommendations for your company stage, and produces an actionable report with direct links to the relevant Microsoft Learn documentation.

## The Solution

An AI agent (powered by GitHub Copilot + Azure MCP Server) that:

1. **Connects** to your Azure subscription (read-only, via Azure MCP Server)
2. **Discovers** everything deployed — resources, configurations, policies, networking, RBAC, security, monitoring
3. **Assesses** against best practices across all 5 WAF pillars + Cloud Adoption Framework + Azure Landing Zone patterns
4. **Contextualizes** recommendations based on your environment profile (startup, scale-up, enterprise)
5. **Reports** by generating a self-contained HTML dashboard with findings, severity, remediation guidance, and direct links to Microsoft Learn documentation for each issue

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  User (GitHub Copilot / Copilot CLI / VS Code)              │
│                                                             │
│  "Assess my Azure subscription"                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Azure Environment Advisor Agent                            │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │ Discovery    │  │ Assessment   │  │ Report             │ │
│  │ Engine       │→ │ Engine       │→ │ Generator          │ │
│  │              │  │              │  │                    │ │
│  │ • Resources  │  │ • WAF Rules  │  │ • HTML dashboard   │ │
│  │ • Configs    │  │ • CAF Rules  │  │ • Severity scores  │ │
│  │ • Policies   │  │ • ALZ Rules  │  │ • MS Learn links   │ │
│  │ • Networking │  │ • Custom     │  │ • Pillar breakdown │ │
│  │ • RBAC       │  │   Rules      │  │ • Filters          │ │
│  │ • Defender   │  │              │  │                    │ │
│  │ • Monitoring │  │ Contextual:  │  │                    │ │
│  │ • Budgets    │  │ • Stage      │  │                    │ │
│  │              │  │ • Size       │  │                    │ │
│  │              │  │ • Complexity │  │                    │ │
│  └─────────────┘  └──────────────┘  └────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Azure MCP Server (Read-Only Access)                        │
│                                                             │
│  Tools used:                                                │
│  • Resource Graph queries (inventory)                       │
│  • Resource configurations (detailed settings)              │
│  • Policy assignments & compliance state                    │
│  • Network topology (VNets, NSGs, peerings, route tables)   │
│  • Defender for Cloud (plans, secure score, recommendations)│
│  • RBAC role assignments                                    │
│  • Diagnostic settings                                      │
│  • Budget & cost data                                       │
│  • Entra ID (groups, conditional access, MFA status)        │
└─────────────────────────────────────────────────────────────┘
```

## Assessment Pillars

The agent assesses across all 5 Well-Architected Framework pillars, plus governance and cost:

### 1. Reliability
- Are zone-redundant SKUs used for critical resources?
- Is there database replication (geo-replica, failover groups)?
- Are health probes and autoscaling configured?
- Is GRS/ZRS used for critical storage?
- Are backups configured and tested?
- Is there a multi-region strategy (if needed)?
- Are SLA targets achievable with current architecture?

### 2. Security
- Is Defender for Cloud enabled? Which plans?
- Are NSGs on every subnet? Do they default to deny-all inbound?
- Is RBAC using groups or direct user assignments?
- Are there public endpoints on databases/storage?
- Is MFA enabled (Security Defaults or Conditional Access)?
- Is Key Vault used for secrets (vs. app settings/env vars)?
- Are managed identities used for Azure-to-Azure auth?
- Is there a break-glass account?
- Are diagnostic settings forwarding security logs?

### 3. Cost Optimization
- Are budget alerts configured?
- Are resources tagged for cost allocation?
- Are there orphaned/unused resources (unattached disks, idle public IPs)?
- Could reserved instances save money on steady-state workloads?
- Are dev/test resources using appropriate SKUs (not production-grade)?
- Is there cost anomaly detection?

### 4. Operational Excellence
- Is IaC used (Bicep/Terraform) or are resources manually created?
- Are there CI/CD pipelines for deployments?
- Is Activity Log forwarded to Log Analytics?
- Are there alert rules for critical operations?
- Is there a tagging strategy with enforcement?
- Are Azure Policy assignments in place?

### 5. Performance Efficiency
- Are resources right-sized (Azure Advisor recommendations)?
- Is caching in use where appropriate (Redis, CDN)?
- Are databases using appropriate service tiers?
- Is auto-scaling configured for compute resources?
- Are resources deployed in the closest region to users?

### 6. Governance
- Is there a management group structure?
- Is subscription topology appropriate (prod/nonprod separation)?
- Are Azure Policies enforcing baseline standards?
- How does the current state compare to Azure Landing Zone patterns?
- What's the recommended graduation path based on current complexity?

## How It Works

### Step 1: Connect
The user points the agent at their Azure subscription. The agent uses the Azure MCP Server for read-only access — no write permissions required for assessment.

```
User: "Assess my Azure subscription abc-12345"
Agent: "Connecting via Azure MCP Server... Scanning resources..."
```

### Step 2: Discover
The agent runs a series of Azure Resource Graph queries and API calls to build a complete picture:

```kusto
// Resource inventory
resources
| summarize count() by type, location, resourceGroup
| order by count_ desc

// Network topology
resources
| where type =~ "microsoft.network/virtualnetworks"
| extend subnets = properties.subnets
| mv-expand subnet = subnets
| project name, addressSpace=properties.addressSpace.addressPrefixes,
          subnetName=subnet.name, subnetPrefix=subnet.properties.addressPrefix

// Security posture
securityresources
| where type == "microsoft.security/securescores"
| project name, properties.score.current, properties.score.max

// Policy compliance
policyresources
| where type == "microsoft.policyinsights/policystates"
| where properties.complianceState == "NonCompliant"
| summarize count() by tostring(properties.policyDefinitionName)

// RBAC assignments
authorizationresources
| where type == "microsoft.authorization/roleassignments"
| extend principalType = properties.principalType
| summarize count() by tostring(principalType), tostring(properties.roleDefinitionId)
```

### Step 3: Profile
Based on what it discovers, the agent determines the environment profile:

| Signal | Startup (5-50 eng) | Scale-up (50-200 eng) | Enterprise (200+ eng) |
|---|---|---|---|
| Subscriptions | 1-2 | 3-10 | 10+ |
| Management Groups | 0-1 | 1-3 | 3+ nested levels |
| Workloads | 1-2 | 3-10 | 10+ |
| Regions | 1 | 1-2 | 2+ |
| Hub network | No | Maybe | Yes |
| Platform team | No | Starting | Dedicated |

### Step 4: Assess & Report
The agent produces a findings report organized by severity and pillar:

```
╔══════════════════════════════════════════════════════════════╗
║  AZURE ENVIRONMENT ASSESSMENT REPORT                        ║
║  Subscription: contoso-prod (abc-12345)                     ║
║  Profile: Startup (estimated 10-20 engineers)               ║
║  Date: 2026-03-06                                           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  SUMMARY                                                     ║
║  ● Critical: 3    ● High: 5    ● Medium: 8    ● Low: 4     ║
║                                                              ║
║  CRITICAL FINDINGS                                           ║
║                                                              ║
║  [SEC-001] Azure SQL has public endpoint enabled             ║
║  Pillar: Security | Resource: sql-contoso-prod               ║
║  Risk: Database accessible from internet                     ║
║  Fix: Enable Private Endpoint + disable public access        ║
║  → docs.microsoft.com/azure/private-link/...                 ║
║                                                              ║
║  [SEC-002] Defender for Cloud not enabled                    ║
║  Pillar: Security | Scope: Subscription                      ║
║  Risk: No threat detection, no secure score                  ║
║  Fix: Enable CSPM (free) + Servers P2 (prod)                ║
║  → docs.microsoft.com/azure/defender-for-cloud/...           ║
║                                                              ║
║  [OPS-001] No diagnostic settings configured                 ║
║  Pillar: Operational Excellence | Scope: Subscription        ║
║  Risk: No audit trail, no visibility into operations         ║
║  Fix: Deploy Log Analytics + Activity Log forwarding         ║
║  → docs.microsoft.com/azure/azure-monitor/...                ║
║                                                              ║
║  HIGH FINDINGS                                               ║
║  ...                                                         ║
╚══════════════════════════════════════════════════════════════╝
```

### Step 5: Generate Dashboard
The agent produces a self-contained HTML dashboard — a single file you can open in any browser, share via email, or attach to a compliance review. No server required.

```
Agent: "Assessment complete. 16 findings across 5 pillars. Generating dashboard..."
Agent: [generates assessment-report.html]
Agent: "Dashboard saved. Open it in your browser to explore findings."
```

The dashboard includes:
- **Executive summary** with finding counts by severity
- **Pillar score cards** with visual scores per WAF pillar
- **Findings list** filterable by pillar and severity
- **Each finding** explains what was found, why it matters, and links directly to the relevant Microsoft Learn documentation for remediation
- **Export options** — print to PDF, share as a single HTML file

## Knowledge Base Structure

The agent's intelligence comes from a `.github/copilot-instructions.md` file that encodes best-practice rules. Rules are organized as assessable checks:

```markdown
## Assessment Rule: SEC-001 — Public Database Endpoints

**Pillar:** Security
**Severity:** Critical
**Check:** Query all SQL/PostgreSQL/MySQL/Cosmos DB resources. If `publicNetworkAccess` is `Enabled` and no Private Endpoint exists → flag.
**Recommendation:** Enable Private Endpoint on `snet-data` subnet, disable public network access.
**Context:**
- Startup: Flag as High (may need public access during early development)
- Scale-up/Enterprise: Flag as Critical
**Learn More:** [Microsoft Learn link for remediation guidance]
```

## Project Structure

```
azure-environment-advisor/
├── .github/
│   ├── copilot-instructions.md       # Agent behavior + assessment methodology
│   ├── ISSUE_TEMPLATE/
│   │   ├── new-rule-request.yml      # Template: propose a new assessment rule
│   │   ├── false-positive.yml        # Template: report a false positive finding
│   │   └── bug-report.yml            # Template: report a bug
│   └── workflows/
│       ├── validate-rules.yml        # CI: validates rule files on every PR
│       └── scheduled-assessment.yml  # Scheduled periodic assessments
├── rules/
│   ├── security/
│   │   ├── defender-plans.md          # Defender for Cloud assessment rules
│   │   ├── network-security.md        # NSG, public endpoints, firewall rules
│   │   ├── identity.md                # RBAC, MFA, break-glass, PIM
│   │   └── secrets.md                 # Key Vault, managed identities
│   ├── reliability/
│   │   ├── zone-redundancy.md         # Zone-redundant SKUs
│   │   ├── backup-recovery.md         # Backup policies, geo-replication
│   │   ├── high-availability.md       # Autoscaling, health probes, failover
│   │   └── disaster-recovery.md       # Multi-region, RPO/RTO analysis
│   ├── cost/
│   │   ├── budget-alerts.md           # Budget configuration
│   │   ├── orphaned-resources.md      # Unused disks, IPs, NICs
│   │   ├── right-sizing.md            # Over-provisioned resources
│   │   └── reservations.md            # RI/savings plan candidates
│   ├── operations/
│   │   ├── monitoring.md              # Log Analytics, diagnostic settings
│   │   ├── policy-governance.md       # Azure Policy, tagging
│   │   ├── iac-ci-cd.md               # IaC usage, pipeline detection
│   │   └── alerting.md                # Alert rules, action groups
│   ├── performance/
│   │   ├── compute-sizing.md          # VM/App Service/AKS sizing
│   │   ├── caching.md                 # Redis, CDN usage
│   │   └── database-tiers.md          # DTU vs vCore, service tiers
│   └── governance/
│       ├── landing-zone-maturity.md   # Landing zone maturity assessment
│       ├── subscription-topology.md   # Sub organization assessment
│       └── management-groups.md       # MG hierarchy assessment
├── queries/
│   ├── resource-graph/                # Azure Resource Graph queries
│   │   ├── inventory.kql
│   │   ├── networking.kql
│   │   ├── security.kql
│   │   ├── compliance.kql
│   │   └── rbac.kql
│   └── log-analytics/                 # KQL queries for log assessment
│       ├── sign-in-anomalies.kql
│       ├── resource-changes.kql
│       └── security-events.kql
├── profiles/
│   ├── startup.md                     # Assessment context for startups (5-50 eng)
│   ├── scaleup.md                     # Assessment context for scale-ups (50-200 eng)
│   └── enterprise.md                  # Assessment context for enterprise (200+ eng)
├── scripts/
│   ├── setup.sh                       # Quick setup — creates .vscode/mcp.json
│   ├── validate-rules.py              # Rule file validation (CI + local)
│   ├── create-issues-from-report.py   # Create GitHub Issues from findings
│   └── compare-assessments.py         # Drift detection between baselines
├── baselines/
│   ├── baseline-schema.json           # JSON schema for assessment baselines
│   └── example-baseline.json          # Example baseline for reference
├── compliance/
│   └── mapping.json                   # Rule-to-compliance-framework mapping
├── samples/
│   └── sample-report.html             # Example assessment report
└── README.md
```

## Differentiators vs. Existing Tools

| Feature | Azure Advisor | Defender | WAF Review | This Agent |
|---|---|---|---|---|
| Scans actual resources | ✅ | ✅ (security only) | ❌ (self-reported) | ✅ |
| All WAF pillars | Partial | Security only | ✅ (manual) | ✅ (automated) |
| Stage-aware recommendations | ❌ | ❌ | ❌ | ✅ |
| Links to MS Learn docs per finding | ❌ | ❌ | ❌ | ✅ |
| Landing zone maturity assessment | ❌ | ❌ | ❌ | ✅ |
| Conversational (ask follow-ups) | ❌ | ❌ | ❌ | ✅ |
| Compares to ALZ landing zone patterns | ❌ | ❌ | ❌ | ✅ |
| Open source / extensible rules | ❌ | ❌ | ❌ | ✅ |
| Works offline (no Azure portal) | ❌ | ❌ | ❌ | ✅ (via MCP) |

## Technical Requirements

- **Azure MCP Server** — for read-only subscription access
- **GitHub Copilot** (CLI, VS Code, or coding agent) — as the AI runtime
- **Azure permissions** — Reader role on subscription(s) to assess
- **No write access needed** — the agent only reads your environment and generates a report

## Getting Started

### How It Works (Key Concepts)

Before you begin, here's what each piece does:

- **GitHub Copilot** is an AI assistant built into VS Code (and the GitHub CLI). You type a request in plain English, and it executes multi-step tasks for you. In **Agent mode**, Copilot can use external tools — like the Azure MCP Server — to read data and act on it.
- **MCP (Model Context Protocol)** is an open standard that lets AI assistants connect to external systems. Think of it as a "plugin" that gives Copilot the ability to read your Azure subscription.
- **Azure MCP Server** is the specific MCP plugin for Azure. It gives Copilot **read-only** access to your subscription's resources, configurations, and policies — it cannot modify anything.
- **This repository** contains the assessment rules, queries, and report template. When you ask Copilot to "assess my Azure subscription," it reads these files, connects to Azure via MCP, and generates an HTML report.

### 1. Prerequisites

| Requirement | What it is | Install link |
|---|---|---|
| **Azure subscription** | The Azure environment you want to assess. If you don't have one, [create a free Azure account](https://azure.microsoft.com/free/) ($200 free credit for 30 days). | [azure.microsoft.com/free](https://azure.microsoft.com/free/) |
| **GitHub Copilot** | AI assistant subscription (Individual, Business, or Enterprise). Needed to run the agent. | [github.com/features/copilot](https://github.com/features/copilot) |
| **VS Code** | The recommended editor. Install the **GitHub Copilot** and **GitHub Copilot Chat** extensions from the Extensions marketplace (`Ctrl+Shift+X` → search "GitHub Copilot"). | [code.visualstudio.com](https://code.visualstudio.com/) |
| **Node.js** (v18+) | Required to run the Azure MCP Server. If using the Copilot CLI, you need v24+. | [nodejs.org](https://nodejs.org/) |
| **Git** | To clone this repository. | [git-scm.com](https://git-scm.com/) |

### 2. Install Azure CLI and Log In

The Azure MCP Server authenticates using your Azure CLI credentials. Install it for your platform:

- **Windows:** `winget install -e --id Microsoft.AzureCLI`
- **macOS:** `brew install azure-cli`
- **Linux:** [Install Azure CLI on Linux](https://learn.microsoft.com/cli/azure/install-azure-cli-linux)

Then log in and verify access:

```bash
# Verify Azure CLI installed correctly (should print version number)
az --version

# Log in — this opens a browser window. Sign in with your Azure account, then return to the terminal.
az login

# List your subscriptions (pick the one you want to assess)
az account list --query "[].{Name:name, Id:id, State:state}" -o table

# Set your target subscription (replace with the Name or ID from above)
az account set --subscription "My Subscription Name"

# Confirm it's active
az account show --query "{Name:name, Id:id, State:state}" -o table
```

> **Permissions:** You need at least **Reader** role on the subscription. No write access is needed — the agent only reads your environment. To check your role:
> ```bash
> az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv) --query "[].{Role:roleDefinitionName, Scope:scope}" -o table
> ```
> If you don't see "Reader" (or a higher role like "Contributor" / "Owner"), ask your Azure administrator to assign the [Reader](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles#reader) built-in role to your account on the target subscription. Role assignments can take up to 5 minutes to take effect.

### 3. Install Azure MCP Server

The simplest approach is to let VS Code handle it automatically via the MCP config (next step). But if you want to install globally:

```bash
npm install -g @azure/mcp
```

> **Note:** Check the [Azure MCP Server documentation](https://learn.microsoft.com/azure/developer/azure-mcp-server/get-started) for the latest installation instructions. For VS Code, you can also install the [Azure MCP Server Extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azure-mcp-server) directly — no npm install needed.

### 4. Clone This Repository

```bash
git clone https://github.com/ricmmartins/azure-environment-advisor.git
cd azure-environment-advisor
```

### 5. Configure MCP Server

The MCP configuration tells Copilot where to find the Azure MCP Server and which subscription to use. Replace `<your-subscription-id>` with the subscription ID from step 2 (the `Id` column from `az account show`).

**For VS Code (recommended):**

Create a file called `mcp.json` inside a `.vscode` folder in the cloned repo:

```
azure-environment-advisor/
  .vscode/
    mcp.json       ← create this file
```

If the `.vscode/` folder doesn't exist, create it first:
- **Windows (PowerShell):** `mkdir .vscode`
- **macOS / Linux:** `mkdir -p .vscode`

Then create `.vscode/mcp.json` with this content:

```json
{
  "servers": {
    "azure": {
      "command": "npx",
      "args": ["-y", "@azure/mcp@latest", "server", "start"],
      "env": {
        "AZURE_SUBSCRIPTION_ID": "<your-subscription-id>"
      }
    }
  }
}
```

> **How VS Code picks this up:** VS Code automatically detects `.vscode/mcp.json` when you open the project folder. No extra settings needed — just restart VS Code after creating the file.

**Alternative — For GitHub Copilot CLI:**

> **Important:** The Copilot CLI with agent mode requires the **new** Copilot CLI, not the legacy `gh-copilot` extension. If you have the old extension installed, remove it first:
> ```bash
> gh extension remove gh-copilot
> ```

Install the GitHub CLI if you haven't, then run `gh copilot` — it will automatically download the new Copilot CLI:
```bash
# Install GitHub CLI: https://cli.github.com/
gh auth login
gh copilot  # Downloads the new Copilot CLI on first run
```

Then create the MCP config file at:
- **macOS / Linux:** `~/.config/github-copilot/mcp.json`
- **Windows:** `%APPDATA%\github-copilot\mcp.json` (typically `C:\Users\YourName\AppData\Roaming\github-copilot\mcp.json`)

Create the directory and file if they don't exist:

```bash
# macOS / Linux
mkdir -p ~/.config/github-copilot
# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path "$env:APPDATA\github-copilot"
```

Then add the same JSON content as above.

### 6. Open in VS Code

Open the project folder in VS Code so that Copilot can read the rules, queries, and profiles — and detect the MCP configuration:

```bash
code .
```

> If `code .` doesn't work, open VS Code manually, then use **File → Open Folder** and select the `azure-environment-advisor` folder.

### 7. Run the Assessment

**In VS Code (recommended):**

1. Open **Copilot Chat** (`Ctrl+Shift+I` on Windows/Linux, `Cmd+Shift+I` on macOS)
2. Make sure you're in **Agent mode** — look for the mode selector at the top of the chat panel. If it says "Ask" or "Edit", click it and switch to **"Agent"**
3. Type your request:

```
Assess my Azure subscription
```

Copilot will read the `.github/copilot-instructions.md` file, connect to Azure via the MCP Server, and start the 5-phase assessment.

**Alternative — In GitHub Copilot CLI:**

From the project directory (requires the new Copilot CLI and Node.js v24+):
```bash
# Non-interactive prompt mode (--allow-all auto-approves tool permissions)
gh copilot -p "Assess my Azure subscription using the rules in this project" --allow-all

# Or start interactive mode (you approve each permission manually)
gh copilot -i
# Then type: Assess my Azure subscription
```

> **Note:** Make sure you're authenticated to Azure (`az login`) before running the assessment.

**What to expect:**

The agent will show its progress as it works:
1. ✅ Connect to your subscription via Azure MCP Server (~30 seconds)
2. 📊 Run the Resource Graph queries from `queries/` (~1 minute)
3. 🏢 Profile your environment (startup / scale-up / enterprise)
4. 🔍 Evaluate against all rules in `rules/` (~2–5 minutes)
5. 📄 Generate a self-contained HTML dashboard

**Expected duration:** 3–5 minutes for small subscriptions (< 50 resources), 5–10 minutes for medium (50–500), 10–15 minutes for large (500+).

### 8. View the Report

When the assessment finishes, Copilot creates a single HTML file in the project folder, e.g.:

```
azure-environment-advisor/
  assessment-contoso-prod-2025-01-15.html    ← your report
```

Open it in any browser (double-click the file, or right-click → "Open with" → your browser). No server required. You can:
- **Share it** via email or Slack (it's a single self-contained file)
- **Print to PDF** using your browser's print function (`Ctrl+P`)
- **Attach it** to a compliance review or architecture decision record

> **What the report looks like:** See the [live sample report](https://htmlpreview.github.io/?https://github.com/ricmmartins/azure-environment-advisor/blob/main/samples/sample-report.html) to preview the interactive dashboard. Your report will have the same layout with findings specific to your subscription.

### Troubleshooting

| Problem | Solution |
|---|---|
| `az login` opens a browser but nothing happens | Make sure you're signing in with the Azure account that has access to the target subscription. After signing in, return to the terminal — it should show "You have logged in." |
| `az account list` shows no subscriptions | Your account may not have any subscriptions. Check with your Azure administrator, or [create a free account](https://azure.microsoft.com/free/). |
| 403 Forbidden / "does not have authorization" | The account you're signed in with doesn't have access to the subscription ID in your MCP config. Run `az account list --output table` to see which subscriptions you can access, then update the `AZURE_SUBSCRIPTION_ID` in your MCP config to match. |
| VS Code uses a different account than the CLI | VS Code and `az login` maintain **separate sessions**. Press `F1` → "Azure: Sign Out", then `F1` → "Azure: Sign In" (or "Azure: Sign In to Directory..." to pick a specific tenant). After signing in, restart the MCP server or reload VS Code. |
| Multi-tenant: signed in but can't see the subscription | If your account has access to multiple tenants, you may be signed into the wrong one. In the CLI: `az login --tenant <tenant-id>`. In VS Code: `F1` → "Azure: Sign In to Directory..." and select the correct tenant. |
| `npm install -g @azure/mcp` fails | Make sure Node.js v18+ is installed (`node --version`). On macOS/Linux you may need `sudo`. |
| Copilot doesn't seem to connect to Azure | Verify the MCP config: check that `.vscode/mcp.json` exists, the subscription ID is correct, and you've restarted VS Code. Try `az account show` to confirm you're logged in. |
| Copilot says "I can't access Azure" or times out | Run `az login` again — your token may have expired. Also verify `AZURE_SUBSCRIPTION_ID` in your MCP config matches the subscription from `az account show`. |
| The report is missing findings or seems incomplete | Large subscriptions may hit Copilot's context limits. Try assessing one resource group at a time: "Assess the resources in resource group rg-production". |
| "Agent mode" not available in VS Code | Make sure the **GitHub Copilot Chat** extension is installed and you have a Copilot subscription. Update VS Code to the latest version. Agent mode requires VS Code 1.99+. |
| `gh copilot` requires Node.js v24+ | The Copilot CLI needs Node.js v24 or higher. Upgrade with `nvm install 24 && nvm use 24`. |
| `gh copilot` → "unknown command" | Your GitHub CLI is too old. Update to gh 2.49+ (`sudo apt upgrade gh` or reinstall from https://cli.github.com). |
| Old `gh-copilot` extension conflicts | If you previously installed `gh extension install github/gh-copilot`, remove it: `gh extension remove gh-copilot`. The new Copilot CLI is built-in. |

### Customization

**Add your own rules:** Create a new `.md` file in the appropriate `rules/` subfolder following the existing format. The agent automatically picks up all rules. Use the [New Rule Request](../../issues/new?template=new-rule-request.yml) issue template to propose rules.

**Adjust severity for your context:** Edit the profile files in `profiles/` to change how severity is calibrated for your company stage.

**Modify queries:** Add or edit `.kql` files in `queries/resource-graph/` to expand what the agent discovers.

**Validate your changes:** Run the rule validation script to ensure your changes are consistent:

```bash
python scripts/validate-rules.py --verbose
```

## Drift Detection

Track how your Azure environment evolves over time by comparing assessment baselines.

### How It Works

1. Each assessment generates a **JSON baseline** file in `baselines/` (alongside the HTML report)
2. Run the comparison script to see what changed between two assessments:

```bash
python scripts/compare-assessments.py \
  --baseline baselines/baseline-2026-01-15.json \
  --current baselines/baseline-2026-02-15.json
```

3. The report shows:
   - 🆕 **New findings** — issues that appeared since the last assessment
   - ✅ **Resolved findings** — issues that were fixed
   - ⬆️ **Escalated** — severity increased (e.g., Medium → High)
   - ⬇️ **De-escalated** — severity decreased
   - ➡️ **Unchanged** — still present with same severity

### CI/CD Integration

Use `--fail-on-regression` to fail a CI pipeline if new Critical/High findings appear:

```bash
python scripts/compare-assessments.py \
  --baseline baselines/baseline-previous.json \
  --current baselines/baseline-current.json \
  --fail-on-regression
```

The baseline schema is defined in `baselines/baseline-schema.json` with an example in `baselines/example-baseline.json`.

## Auto-Create GitHub Issues

Convert assessment findings into trackable GitHub Issues automatically:

```bash
# Preview what would be created (dry run)
python scripts/create-issues-from-report.py --report assessment-report.html --dry-run

# Create issues for Critical and High findings (default)
python scripts/create-issues-from-report.py --report assessment-report.html

# Create issues for all severities
python scripts/create-issues-from-report.py --report assessment-report.html --severity Critical High Medium Low

# Add custom labels
python scripts/create-issues-from-report.py --report assessment-report.html --labels "sprint-1,team-platform"
```

Each issue includes:
- Rule ID and title
- Severity and pillar labels
- Affected resources
- Remediation guidance
- Microsoft Learn documentation links

> **Requirement:** GitHub CLI (`gh`) must be installed and authenticated.
>
> **See it in action:** Check out the [example issues](https://github.com/ricmmartins/azure-environment-advisor/issues) created from a real assessment run.

## Compliance Framework Mapping

Findings are mapped to controls in 5 compliance frameworks:

| Framework | Coverage |
|-----------|----------|
| **SOC2** | Trust Services Criteria (CC, A1) |
| **ISO 27001** | ISO/IEC 27001:2022 Annex A controls |
| **HIPAA** | §164.308, §164.310, §164.312 |
| **PCI-DSS** | PCI DSS v4.0 requirements |
| **NIST CSF** | NIST Cybersecurity Framework 2.0 functions |

The mapping is stored in `compliance/mapping.json` and is automatically included in the assessment report. Each finding card shows which compliance controls are impacted, and the report includes a Compliance Summary section.

> **Note:** This mapping is a guidance aid for audit preparation — it is not a formal compliance assessment or certification.

## Contributing

We welcome contributions! Here's how:

1. **Propose a new rule** — Use the [New Rule Request](../../issues/new?template=new-rule-request.yml) issue template
2. **Report a false positive** — Use the [False Positive](../../issues/new?template=false-positive.yml) issue template
3. **Report a bug** — Use the [Bug Report](../../issues/new?template=bug-report.yml) issue template
4. **Submit a PR** — The `validate-rules.yml` workflow will automatically validate your rule files

### Rule Validation

All rule files are validated on every PR by the CI pipeline. You can also run validation locally:

```bash
# Text output with warnings
python scripts/validate-rules.py --verbose

# JSON output (for programmatic use)
python scripts/validate-rules.py --output json
```

The validator checks:
- Required sections (`What to Check`, `Finding Template`, `Learn More`)
- Valid rule ID format (e.g., `SEC-001`, `REL-010`)
- Pillar consistency (rule prefix matches declared pillar)
- Severity values
- Profile coverage (every rule should appear in profile severity tables)

## Glossary

| Term | Definition |
|------|-----------|
| **WAF** | [Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/) — Microsoft's 5-pillar framework for building reliable, secure, efficient, cost-optimized, and operationally excellent workloads |
| **CAF** | [Cloud Adoption Framework](https://learn.microsoft.com/azure/cloud-adoption-framework/) — Microsoft's guidance for cloud adoption strategy, planning, and governance |
| **ALZ** | [Azure Landing Zone](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/) — A target architecture for enterprise Azure environments with management groups, networking, and governance |
| **MCP** | [Model Context Protocol](https://modelcontextprotocol.io/) — An open protocol that allows AI agents to connect to external tools and data sources |
| **NSG** | Network Security Group — Azure's network-level firewall for controlling traffic to/from subnets and VMs |
| **RBAC** | Role-Based Access Control — Azure's authorization system for managing who can do what on which resources |
| **PIM** | Privileged Identity Management — Entra ID feature for just-in-time privileged access |
| **CSPM** | Cloud Security Posture Management — Defender for Cloud's free tier for security recommendations |
| **MFA** | Multi-Factor Authentication — Requiring two or more verification methods for sign-in |
| **KQL** | Kusto Query Language — The query language used by Azure Resource Graph and Log Analytics |

## Future Possibilities

- **Multi-subscription assessment** — scan all subs under a management group
- **Team recommendations** — suggest organizational changes (when to hire a platform team)
- **Trend dashboards** — visualize drift detection results over time in a web dashboard
- **Rule marketplace** — community-contributed rule packs for specific industries (healthcare, finance, gaming)
- **Integration with Azure Monitor** — correlate findings with actual availability/performance metrics
- **AI-powered remediation** — generate IaC (Bicep/Terraform) patches to fix findings automatically

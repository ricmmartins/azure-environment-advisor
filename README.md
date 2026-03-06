# Azure Environment Advisor

An AI-powered agent that authenticates to your Azure subscription, assesses your environment against best practices, and generates actionable remediation code — tailored to your company's stage and architecture.

## The Problem

Teams deploying on Azure today face a fragmented landscape of advisory tools:

| Tool | Covers | Limitation |
|---|---|---|
| Azure Advisor | Cost, reliability, security, performance | Generic recommendations, no context about your stage or architecture |
| Defender for Cloud | Security posture (Secure Score) | Security-only, no reliability/cost/networking holistic view |
| WAF Assessment | Well-Architected review (all 5 pillars) | Manual questionnaire — self-reported, doesn't scan actual resources |
| Azure Resource Graph | Resource inventory queries | Raw data — no intelligence or recommendation layer |
| Cost Management | Spending analysis + budget alerts | Cost-only, no connection to architecture decisions |

**The gap:** No single tool connects to your actual environment, assesses it holistically across all Well-Architected pillars, contextualizes recommendations for your company stage, and generates IaC code to fix what it finds.

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
│  │ Discovery    │  │ Assessment   │  │ Remediation        │ │
│  │ Engine       │→ │ Engine       │→ │ Engine             │ │
│  │              │  │              │  │                    │ │
│  │ • Resources  │  │ • WAF Rules  │  │ • Bicep generator  │ │
│  │ • Configs    │  │ • CAF Rules  │  │ • Terraform gen    │ │
│  │ • Policies   │  │ • ALZ Rules  │  │ • Script gen       │ │
│  │ • Networking │  │ • Custom     │  │ • Priority order   │ │
│  │ • RBAC       │  │   Rules      │  │                    │ │
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

### 6. Governance & Landing Zone
- Is there a management group structure?
- Is subscription topology appropriate (prod/nonprod separation)?
- Are Azure Policies enforcing baseline standards?
- How does the current state compare to SSLZ / Trey Research / full ALZ?
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
║  → Remediation code generated (Bicep + Terraform)            ║
║                                                              ║
║  [SEC-002] Defender for Cloud not enabled                    ║
║  Pillar: Security | Scope: Subscription                      ║
║  Risk: No threat detection, no secure score                  ║
║  Fix: Enable CSPM (free) + Servers P2 (prod)                ║
║  → Remediation code generated (Bicep + Terraform)            ║
║                                                              ║
║  [OPS-001] No diagnostic settings configured                 ║
║  Pillar: Operational Excellence | Scope: Subscription        ║
║  Risk: No audit trail, no visibility into operations         ║
║  Fix: Deploy Log Analytics + Activity Log forwarding         ║
║  → Remediation code generated (Bicep + Terraform)            ║
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
**Remediation:** [Bicep template] [Terraform template]
```

## Project Structure

```
azure-environment-advisor/
├── .github/
│   └── copilot-instructions.md       # Agent behavior + assessment methodology
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
│       ├── landing-zone-maturity.md   # SSLZ vs Trey Research vs full ALZ
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
├── remediation/
│   ├── bicep/                         # Bicep remediation templates
│   │   ├── enable-defender.bicep
│   │   ├── configure-nsg.bicep
│   │   ├── setup-diagnostics.bicep
│   │   ├── configure-budget.bicep
│   │   └── ...
│   └── terraform/                     # Terraform remediation templates
│       ├── enable-defender.tf
│       ├── configure-nsg.tf
│       ├── setup-diagnostics.tf
│       ├── configure-budget.tf
│       └── ...
├── profiles/
│   ├── startup.md                     # Assessment context for startups (5-50 eng)
│   ├── scaleup.md                     # Assessment context for scale-ups (50-200 eng)
│   └── enterprise.md                  # Assessment context for enterprise (200+ eng)
├── docs/
│   ├── getting-started.md
│   ├── how-it-works.md
│   ├── adding-rules.md
│   └── azure-mcp-setup.md
├── README.md
└── LICENSE
```

## Differentiators vs. Existing Tools

| Feature | Azure Advisor | Defender | WAF Review | This Agent |
|---|---|---|---|---|
| Scans actual resources | ✅ | ✅ (security only) | ❌ (self-reported) | ✅ |
| All WAF pillars | Partial | Security only | ✅ (manual) | ✅ (automated) |
| Stage-aware recommendations | ❌ | ❌ | ❌ | ✅ |
| Generates IaC remediation | ❌ | ❌ | ❌ | ✅ |
| Landing zone maturity assessment | ❌ | ❌ | ❌ | ✅ |
| Conversational (ask follow-ups) | ❌ | ❌ | ❌ | ✅ |
| Compares to SSLZ/ALZ patterns | ❌ | ❌ | ❌ | ✅ |
| Open source / extensible rules | ❌ | ❌ | ❌ | ✅ |
| Works offline (no Azure portal) | ❌ | ❌ | ❌ | ✅ (via MCP) |

## Technical Requirements

- **Azure MCP Server** — for read-only subscription access
- **GitHub Copilot** (CLI, VS Code, or coding agent) — as the AI runtime
- **Azure permissions** — Reader role on subscription(s) to assess
- **No write access needed** for assessment — remediation code is generated but applied by the user

## Future Possibilities

- **Multi-subscription assessment** — scan all subs under a management group
- **Drift detection** — compare current state against a baseline (previous assessment)
- **Compliance mapping** — map findings to SOC2/HIPAA/PCI controls
- **Team recommendations** — suggest organizational changes (when to hire a platform team)
- **Integration with Azure DevOps / GitHub Issues** — auto-create work items for findings
- **Scheduled assessments** — periodic re-assessment via GitHub Actions
- **Community rules** — let users contribute assessment rules (like ESLint plugins)

## Relationship to SSLZ

This project is **complementary** to the [Startup-Scale Landing Zone](https://startupscalelanding.zone):

- **SSLZ** = opinionated infrastructure code for deploying a landing zone from scratch
- **Azure Environment Advisor** = assessment tool for evaluating any existing Azure environment

The agent can recommend SSLZ for greenfield startups, Trey Research for small enterprises, or full ALZ for mature organizations — based on what it discovers in the environment.

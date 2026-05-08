# Assessment Data Model

Shared internal representation used by Azure Environment Advisor skills. Defines the structure for findings, passed checks, and assessment metadata.

---

## Finding Schema

Each assessment finding has this structure:

```json
{
  "rule_id": "SEC-001",
  "title": "Microsoft Defender for Cloud is not enabled",
  "pillar": "security",
  "severity": "critical",
  "what_found": "No Defender for Cloud plans are enabled on subscription contoso-prod.",
  "why_matters": "Without Defender for Cloud, the environment has no advanced threat detection.",
  "recommendation": "Enable Defender CSPM (free), then enable Defender for Servers Plan 2.",
  "resources_affected": ["subscription/contoso-prod"],
  "learn_more": [
    {
      "title": "Get started with Microsoft Defender for Cloud",
      "url": "https://learn.microsoft.com/azure/defender-for-cloud/get-started"
    }
  ],
  "compliance_refs": [
    { "framework": "SOC2", "control": "CC6.1", "description": "Logical and Physical Access Controls" }
  ]
}
```

## Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rule_id` | string | Yes | Unique rule identifier (e.g., SEC-001, REL-002) |
| `title` | string | Yes | Clear, specific description of what was found |
| `pillar` | string | Yes | WAF pillar: security, reliability, cost, operations, performance, governance |
| `severity` | string | Yes | **Profile-adjusted** severity: critical, high, medium, low |
| `what_found` | string | Yes | Factual description of the current state with specific resource names |
| `why_matters` | string | Yes | Business impact and risk explanation |
| `recommendation` | string | Yes | Specific, actionable remediation steps |
| `resources_affected` | array | Yes | Resource names, resource groups, or resource IDs affected |
| `learn_more` | array | Yes | 1–3 Microsoft Learn links with title and URL |
| `compliance_refs` | array | No | Compliance framework mappings (added by azea-compliance-map) |
| `remediation` | object | No | ARM template remediation metadata (added by azea-remediate) |

## Pillar Values

| Pillar | Directory | Description |
|--------|-----------|-------------|
| `security` | `rules/security/` | Defender, network security, identity, secrets management |
| `reliability` | `rules/reliability/` | Zone redundancy, backup, high availability, disaster recovery |
| `cost` | `rules/cost/` | Budgets, orphaned resources, right-sizing, reservations |
| `operations` | `rules/operations/` | Monitoring, policy, IaC, alerting |
| `performance` | `rules/performance/` | Compute sizing, caching, database tiers |
| `governance` | `rules/governance/` | Landing zone maturity, subscription topology, management groups |

## Severity Levels

| Level | Meaning |
|-------|---------|
| `critical` | Immediate risk. Data exposure, no security baseline, no disaster recovery for critical data. |
| `high` | Significant gap. Missing best practices that could cause outages, security incidents, or major cost overruns. |
| `medium` | Notable improvement area. Environment works but doesn't follow recommended patterns. |
| `low` | Minor optimization. Nice-to-have improvements, minor cost savings, polish items. |

## Remediation Schema (Optional)

When the `azea-remediate` skill is used, findings may include a remediation object:

```json
{
  "remediation": {
    "type": "arm-template",
    "description": "Enable Private Endpoint for SQL Database",
    "template_source": "generated | provided",
    "resource_group": "rg-contoso-prod",
    "status": "pending | deployed | failed | cancelled",
    "deployment_name": "remediate-SEC-001-2026-05-08",
    "requires_confirmation": true
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Always `arm-template` for ARM MCP Server deployments |
| `description` | string | Human-readable description of the remediation action |
| `template_source` | string | `generated` (AI-created) or `provided` (from a known template) |
| `resource_group` | string | Target resource group for the deployment |
| `status` | string | Deployment status: pending, deployed, failed, cancelled |
| `deployment_name` | string | ARM deployment name for tracking |
| `requires_confirmation` | boolean | Always `true` — remediation never auto-deploys |

## Passed Check Schema

```json
{
  "rule_id": "SEC-012",
  "title": "Storage accounts have public blob access disabled"
}
```

## Assessment Metadata Schema

```json
{
  "subscription_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "subscription_name": "contoso-prod",
  "profile": "scale-up",
  "date": "2026-04-09",
  "total_resources": 127,
  "regions": ["eastus", "westus2"],
  "pillar_scores": {
    "security": 64,
    "reliability": 76,
    "cost": 88,
    "operations": 52,
    "performance": 94,
    "governance": 70
  },
  "finding_counts": {
    "critical": 2,
    "high": 5,
    "medium": 8,
    "low": 3,
    "passed": 22
  }
}
```

## Usage by Skill

| Skill | How it uses the model |
|-------|----------------------|
| `azea-discover` | Produces raw discovery data consumed by assess |
| `azea-profile` | Reads discovery data, produces profile selection |
| `azea-assess` | Produces findings + passed checks + pillar scores |
| `azea-report` | Consumes findings + metadata to generate HTML |
| `azea-baseline` | Serializes findings to JSON for drift detection |
| `azea-compliance-map` | Enriches findings with compliance_refs |
| `azea-remediate` | Uses findings to deploy ARM template remediations |
| `azea-create-issues` | Reads findings to create GitHub Issues |
| `azea-full-assessment` | Orchestrates all of the above |

# Remediation Templates

Infrastructure-as-Code templates that fix specific findings raised by the Azure Environment Advisor. Each template addresses **one rule** and can be deployed independently.

> **⚠️ Review before deploying.** These templates modify your Azure environment. Always inspect parameter values, test in a non-production subscription first, and validate with your team before running against production.

## Available Templates

| Rule ID | Description | Scope | Template |
|---------|-------------|-------|----------|
| **COST-001** | Create subscription budget with spend alerts | Subscription | [`COST-001-create-budget.bicep`](bicep/COST-001-create-budget.bicep) |
| **GOV-011** | Management group hierarchy for prod/non-prod separation | Tenant | [`GOV-011-environment-separation.bicep`](bicep/GOV-011-environment-separation.bicep) |
| **OPS-001** | Log Analytics workspace + Activity Log diagnostic settings | Subscription | [`OPS-001-enable-diagnostics.bicep`](bicep/OPS-001-enable-diagnostics.bicep) |
| **REL-003** | Upgrade storage account replication (LRS → GRS/ZRS) | Resource Group | [`REL-003-storage-replication.bicep`](bicep/REL-003-storage-replication.bicep) |
| **REL-010** | Recovery Services vault + VM backup policy | Resource Group | [`REL-010-enable-backup.bicep`](bicep/REL-010-enable-backup.bicep) |
| **SEC-003** | Defender for Cloud security contact configuration | Subscription | [`SEC-003-security-contact.bicep`](bicep/SEC-003-security-contact.bicep) |
| **SEC-014** | NSG deny rule to block inbound Internet traffic | Resource Group | [`SEC-014-remove-public-ip.bicep`](bicep/SEC-014-remove-public-ip.bicep) |
| **SEC-022** | Enforce MFA (Conditional Access / Security Defaults) | Subscription* | [`SEC-022-enforce-mfa.bicep`](bicep/SEC-022-enforce-mfa.bicep) |

\* SEC-022 uses `az rest` CLI commands because Bicep does not support Microsoft Graph Conditional Access resources natively. The template file contains full instructions.

## Prerequisites

- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) ≥ 2.61
- [Bicep CLI](https://learn.microsoft.com/azure/azure-resource-manager/bicep/install) ≥ 0.28 (bundled with Azure CLI)
- Appropriate RBAC roles on the target scope (Contributor for resource groups, Owner for subscription-level, elevated access for tenant-level)

## Usage

### Resource Group scope

```bash
az deployment group create \
  --resource-group <resource-group> \
  --template-file remediation/bicep/<template>.bicep \
  --parameters param1=value1 param2=value2
```

**Examples:**

```bash
# SEC-014 — Block inbound Internet traffic on an NSG
az deployment group create \
  --resource-group rg-web-prod \
  --template-file remediation/bicep/SEC-014-remove-public-ip.bicep \
  --parameters nsgName=nsg-web-frontend

# REL-010 — Enable backup for VMs
az deployment group create \
  --resource-group rg-compute \
  --template-file remediation/bicep/REL-010-enable-backup.bicep \
  --parameters vaultName=rsv-backup \
               vmNames='["vm-web-01","vm-app-01"]' \
               location=eastus

# REL-003 — Upgrade storage replication to GRS
az deployment group create \
  --resource-group rg-storage \
  --template-file remediation/bicep/REL-003-storage-replication.bicep \
  --parameters storageAccountName=stproddata01
```

### Subscription scope

```bash
az deployment sub create \
  --location <region> \
  --template-file remediation/bicep/<template>.bicep \
  --parameters param1=value1
```

**Examples:**

```bash
# COST-001 — Create a $5,000/month budget with alerts
az deployment sub create \
  --location eastus \
  --template-file remediation/bicep/COST-001-create-budget.bicep \
  --parameters budgetName=budget-monthly \
               amount=5000 \
               contactEmails='["finance@contoso.com","devops@contoso.com"]'

# OPS-001 — Enable Activity Log diagnostics
az deployment sub create \
  --location eastus \
  --template-file remediation/bicep/OPS-001-enable-diagnostics.bicep \
  --parameters workspaceName=law-diagnostics \
               location=eastus \
               retentionDays=90

# SEC-003 — Configure Defender for Cloud security contact
az deployment sub create \
  --location eastus \
  --template-file remediation/bicep/SEC-003-security-contact.bicep \
  --parameters email=security-team@contoso.com \
               phone='+15551234567'
```

### Tenant scope

```bash
# GOV-011 — Create management group hierarchy
az deployment tenant create \
  --location eastus \
  --template-file remediation/bicep/GOV-011-environment-separation.bicep \
  --parameters rootMgName=mg-contoso
```

> Tenant-level deployments require [elevated access](https://learn.microsoft.com/azure/role-based-access-control/elevate-access-global-admin).

### What-If (dry run)

Always preview changes before deploying:

```bash
az deployment group what-if \
  --resource-group <resource-group> \
  --template-file remediation/bicep/<template>.bicep \
  --parameters param1=value1

az deployment sub what-if \
  --location eastus \
  --template-file remediation/bicep/<template>.bicep \
  --parameters param1=value1
```

## Validation with Bicep MCP Server

If you are using the [Bicep MCP Server](https://github.com/Azure/bicep/tree/main/src/Bicep.Local.Extension) or VS Code with the Bicep extension, you can validate templates before deployment:

```bash
# CLI validation
az bicep build --file remediation/bicep/<template>.bicep

# Or use the Bicep linter
az bicep lint --file remediation/bicep/<template>.bicep
```

The Bicep extension in VS Code provides real-time validation, IntelliSense, and linting as you edit templates.

## Template Design Principles

- **One rule, one template** — each file fixes exactly one advisor finding
- **Minimal scope** — templates only touch the resources needed for remediation
- **Parameterised** — all environment-specific values are parameters with sensible defaults
- **Documented** — every parameter has an `@description` decorator; each file includes a header comment with the rule ID, description, and usage example
- **Idempotent** — templates can be re-deployed safely (ARM incremental mode)

## Contributing

When adding a new remediation template:

1. Name the file `<RULE-ID>-<short-description>.bicep`
2. Set the correct `targetScope` (`resourceGroup`, `subscription`, or `tenant`)
3. Add `@description` decorators to all parameters
4. Include a file-level comment block with rule ID, description, and usage example
5. Update the table in this README
6. Test with `az deployment ... what-if` before submitting

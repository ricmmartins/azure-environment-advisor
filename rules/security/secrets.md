# Security Assessment Rules — Secrets Management

Rules for assessing Key Vault usage, secrets handling practices, and managed identity adoption across the Azure environment.

---

## SEC-030 — No Key Vault deployed

**Pillar:** Security
**Severity:** High
**Profiles:** High for all profiles

### What to Check
Query for the existence of any Key Vault resources in the subscription. If no `microsoft.keyvault/vaults` resources exist, the environment has no centralized secrets management.

```kusto
resources
| where type == "microsoft.keyvault/vaults"
| project name, resourceGroup, subscriptionId
```

Flag when the query returns zero results.

### Finding Template
**Title:** No Azure Key Vault deployed in the environment
**What was found:** No Key Vault resources (`microsoft.keyvault/vaults`) were found in subscription `{subscriptionName}`. There is no centralized secrets management service deployed.
**Why it matters:** Without Key Vault, secrets such as database connection strings, API keys, and certificates are typically stored in application settings, configuration files, or environment variables. These locations offer no access auditing, rotation capabilities, or fine-grained access control, and secrets are often exposed in deployment logs and source control.
**Recommendation:** Deploy an Azure Key Vault in each environment (dev, staging, production). Migrate all secrets from App Service/Function App application settings into Key Vault. Use Key Vault references in App Service configuration to securely retrieve secrets at runtime.

### Learn More
- [About Azure Key Vault](https://learn.microsoft.com/azure/key-vault/general/overview) — overview of Key Vault capabilities for secrets, keys, and certificates
- [Best practices for using Azure Key Vault](https://learn.microsoft.com/azure/key-vault/general/best-practices) — recommended patterns for Key Vault deployment and usage

---

## SEC-031 — Key Vault using access policies instead of RBAC

**Pillar:** Security
**Severity:** Medium
**Profiles:** Medium for all profiles

### What to Check
Query Key Vault resources and check the `enableRbacAuthorization` property. When set to `false` or absent, the Key Vault uses the legacy access policy model instead of Azure RBAC.

```kusto
resources
| where type == "microsoft.keyvault/vaults"
| where properties.enableRbacAuthorization == false or isnull(properties.enableRbacAuthorization)
| project name, resourceGroup, subscriptionId, enableRbacAuthorization = properties.enableRbacAuthorization
```

Flag any Key Vault that is not using RBAC authorization.

### Finding Template
**Title:** Key Vault uses access policies instead of Azure RBAC
**What was found:** Key Vault `{vaultName}` in resource group `{resourceGroup}` has `enableRbacAuthorization` set to `false`. The vault uses legacy access policies for authorization instead of Azure RBAC.
**Why it matters:** Access policies are managed separately from the rest of Azure RBAC, creating inconsistency in the authorization model. They lack fine-grained control (no deny assignments, no conditions), cannot be audited through the same tooling as RBAC, and do not support Privileged Identity Management (PIM) for just-in-time access.
**Recommendation:** Migrate the Key Vault to Azure RBAC authorization. Map existing access policies to equivalent RBAC roles (e.g., `Key Vault Secrets User`, `Key Vault Certificates Officer`). Enable RBAC authorization on the vault and verify application access before removing the legacy access policies.

### Learn More
- [Provide access to Key Vault using Azure RBAC](https://learn.microsoft.com/azure/key-vault/general/rbac-guide) — RBAC roles available for Key Vault and how to assign them
- [Migrate from vault access policy to Azure RBAC](https://learn.microsoft.com/azure/key-vault/general/rbac-migration) — step-by-step migration guide from access policies to RBAC

---

## SEC-032 — Managed identities not used

**Pillar:** Security
**Severity:** Medium
**Profiles:** Medium for all profiles

### What to Check
Query compute resources (App Services, Function Apps, AKS clusters, Virtual Machines) and check whether a system-assigned or user-assigned managed identity is enabled. Resources without any managed identity are likely using stored credentials for Azure-to-Azure authentication.

```kusto
resources
| where type in (
    "microsoft.web/sites",
    "microsoft.containerservice/managedclusters",
    "microsoft.compute/virtualmachines"
  )
| where isnull(identity) or identity.type == "None"
| project name, type, resourceGroup, subscriptionId
```

Flag any compute resource that has no managed identity configured.

### Finding Template
**Title:** Compute resource does not use a managed identity
**What was found:** `{resourceType}` resource `{resourceName}` in resource group `{resourceGroup}` does not have a system-assigned or user-assigned managed identity enabled. The resource likely uses stored credentials (connection strings, keys, or secrets) for authenticating to other Azure services.
**Why it matters:** Stored credentials must be manually rotated, can be leaked through configuration exposure, and are difficult to audit. Managed identities eliminate the need for stored credentials by providing automatically managed, short-lived tokens for Azure-to-Azure authentication. This removes an entire class of credential-related security risks.
**Recommendation:** Enable a managed identity on the resource — system-assigned for single-resource scenarios, or user-assigned for shared identity across multiple resources. Grant the managed identity the minimum required RBAC roles on target resources (e.g., `Storage Blob Data Reader` on a storage account). Update application code to use `DefaultAzureCredential` or the equivalent SDK credential chain.

### Learn More
- [What are managed identities for Azure resources?](https://learn.microsoft.com/entra/identity/managed-identities-azure-resources/overview) — overview of managed identity types and supported services
- [Configure managed identities on Azure VMs](https://learn.microsoft.com/entra/identity/managed-identities-azure-resources/qs-configure-portal-windows-vm) — portal-based quickstart for enabling managed identities

# Operations Assessment Rules — IaC & CI/CD

Rules for assessing whether infrastructure-as-code and automated deployment practices are in place to ensure repeatable, auditable deployments.

---

## OPS-020 — No evidence of IaC usage

**Pillar:** Operational Excellence  
**Severity:** Medium  
**Profiles:** startup: Low · scale-up: Medium · enterprise: High

### What to Check
Analyze the deployment history for patterns that suggest manual resource creation. Look for single-resource ARM deployments originating from the Azure portal (correlation IDs from portal, deployment names with random GUIDs typical of portal deployments). Check for the absence of template deployments or deployment stacks.

```kusto
resourcechanges
| where properties.changeAttributes.changedBy contains "portal"
| summarize portalDeployments = count() by
    resourceGroup = tostring(properties.targetResourceId)
| order by portalDeployments desc
```

Also review deployment history via Azure CLI:
```bash
az deployment sub list --query "[].{name:name, timestamp:properties.timestamp, mode:properties.mode}" -o table
```

### Finding Template
**Title:** No evidence of infrastructure-as-code usage  
**What was found:** Analysis of deployment history in subscription `{subscriptionName}` indicates that {portalPercentage}% of deployments originated from the Azure portal or manual CLI commands. No Bicep, Terraform, or multi-resource ARM template deployments were detected.  
**Why it matters:** Manual deployments are error-prone, non-repeatable, and unauditable. Without IaC, you cannot reliably recreate environments for disaster recovery, enforce consistent configurations, or review infrastructure changes through pull requests. Manual deployments are the leading cause of configuration drift between environments.  
**Recommendation:** Adopt Bicep (Azure-native) or Terraform (multi-cloud) for infrastructure deployment. Start by exporting existing resources as templates, then iterate toward fully declarative infrastructure definitions. Store templates in version control and deploy through automated pipelines.

### Learn More
- [What is Bicep?](https://learn.microsoft.com/azure/azure-resource-manager/bicep/overview) — Azure-native domain-specific language for deploying Azure resources declaratively
- [Infrastructure as code](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/considerations/infrastructure-as-code) — Cloud Adoption Framework guidance on IaC adoption strategy

---

## OPS-021 — No CI/CD deployment pattern

**Pillar:** Operational Excellence  
**Severity:** Medium (scale-up/enterprise), Low (startup)  
**Profiles:** startup: Low · scale-up: Medium · enterprise: Medium

### What to Check
Analyze deployment history for patterns indicating all deployments are performed by the same user principal, suggesting manual deployment processes rather than service principal-based CI/CD pipelines.

```kusto
resourcechanges
| extend changedBy = tostring(properties.changeAttributes.changedBy)
| summarize deploymentCount = count() by changedBy
| order by deploymentCount desc
```

Look for the absence of service principal or managed identity-based deployments, which would indicate CI/CD pipeline usage.

### Finding Template
**Title:** No CI/CD deployment pattern detected  
**What was found:** All {deploymentCount} deployments in subscription `{subscriptionName}` over the last 90 days were performed by individual user accounts. No deployments from service principals or managed identities (indicating CI/CD pipelines) were detected. Primary deployer: {topDeployer} ({percentage}% of deployments).  
**Why it matters:** Manual deployments by individual users bypass code review, testing, and approval gates. They cannot be reliably reproduced and create a single-person dependency for deployment knowledge. CI/CD pipelines provide repeatable deployments, audit trails, automated testing, and rollback capabilities.  
**Recommendation:** Set up deployment pipelines using GitHub Actions or Azure DevOps Pipelines. Configure service principals with least-privilege RBAC roles for automated deployments. Implement approval gates for production deployments.

### Learn More
- [Deploy to App Service using GitHub Actions](https://learn.microsoft.com/azure/app-service/deploy-github-actions) — end-to-end guide for CI/CD with GitHub Actions and Azure
- [What is Azure Pipelines?](https://learn.microsoft.com/azure/devops/pipelines/get-started/what-is-azure-pipelines) — overview of Azure DevOps CI/CD pipeline capabilities

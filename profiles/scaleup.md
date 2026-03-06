# Scale-up Profile (50–200 Engineers)

## Detection Signals

| Signal | Threshold |
|--------|-----------|
| Subscriptions | 3–10 |
| Total resources | 50–500 |
| Regions | 1–2 |
| Management groups | Some (or emerging) |
| Hub VNet | Maybe present |

## Philosophy

Scale-ups are in the critical transition from "it just works" to "it needs to work reliably." Recommendations for this profile focus on **formalizing practices, investing in platform team foundations, and thinking about multi-subscription architecture**. Technical debt from the startup phase needs to be addressed before it becomes a blocker.

## What Matters Most

- **Subscription separation** — Prod and non-prod must be in separate subscriptions.
- **Proper RBAC** — Move from direct user assignments to group-based access.
- **Policy governance** — Start enforcing tagging, allowed regions, and resource configurations.
- **Monitoring maturity** — Centralized logging, alerting on critical metrics, and dashboards.
- **DR planning** — Document RPO/RTO targets; begin implementing backup strategies.

## Expectations

- **Prod/non-prod separation** in distinct subscriptions.
- **Conditional Access** for MFA enforcement (graduate from Security Defaults).
- Basic **Azure Policy** assignments (tagging, allowed locations, resource type restrictions).
- **IaC adoption** in progress (Bicep, Terraform, or equivalent).
- At least one platform/infrastructure team member or function.
- Beginning to formalize change management and deployment processes.

## Severity Adjustments

Most rules apply at standard severity. Governance and operational maturity become increasingly important.

| Rule ID | Rule Title | Default Severity | Scale-up Severity | Rationale |
|---------|-----------|-----------------|------------------|-----------|
| **Reliability** | | | | |
| REL-001 | Azure SQL not zone-redundant | High | Medium | Consider for production databases |
| REL-002 | App Service not zone-redundant | High | Medium | Consider for production workloads |
| REL-003 | Storage not using ZRS/GRS | High | High | Production data needs redundancy |
| REL-004 | AKS not using availability zones | High | Medium | Important if AKS is a core platform |
| REL-010 | No backup policy for Azure VMs | Critical | Critical | Backups are non-negotiable |
| REL-011 | SQL Database no long-term retention | Medium | Medium | Standard requirement for compliance |
| REL-012 | No geo-replication for critical databases | High | Medium | Plan for it; implement for critical DBs |
| REL-013 | Blob soft delete not enabled | Medium | Medium | Easy win, should be standard |
| REL-020 | No autoscale configured for compute | High | High | Production workloads need autoscale |
| REL-021 | Load balancer without health probes | High | High | Operational hygiene |
| REL-022 | Single instance VM (no availability) | High | High | Production needs redundancy |
| REL-030 | No multi-region strategy | High | Medium | Begin planning; not yet critical |
| REL-031 | No documented RPO/RTO targets | Medium | High | Must formalize at this stage |
| REL-032 | Site Recovery not configured for VMs | High | Medium | Implement for critical workloads |
| **Security** | | | | |
| SEC-001 | Defender for Cloud not enabled | Critical | Critical | Non-negotiable |
| SEC-002 | Secure Score below 50% | High | High | Target 60%+ |
| SEC-003 | Security contact not configured | Medium | High | Must have a security point of contact |
| SEC-010 | Public database endpoints | Critical | Critical | Non-negotiable |
| SEC-011 | NSG missing on subnet | High | High | Must enforce consistently |
| SEC-012 | Storage account allows public blob access | High | High | Should be disabled org-wide |
| SEC-013 | No Azure Firewall or NVA for egress filtering | Medium | Medium | Evaluate; implement for prod if hub/spoke |
| SEC-014 | Public IP addresses on VMs | Medium | High | Minimize; use Bastion or VPN for access |
| SEC-020 | RBAC uses direct user assignments | High | High | Must transition to group-based RBAC |
| SEC-021 | Too many Owner/Contributor assignments | High | High | Tighten access; principle of least privilege |
| SEC-022 | No MFA enforcement detected | Critical | Critical | Conditional Access required |
| SEC-023 | No break-glass account pattern | Medium | High | Must implement at this scale |
| SEC-030 | No Key Vault deployed | High | High | Standard requirement |
| SEC-031 | Key Vault using access policies instead of RBAC | Medium | Medium | Plan migration to RBAC model |
| SEC-032 | Managed identities not used | Medium | High | Should be the default for service auth |

## Recommended Landing Zone

**[Trey Research](https://aka.ms/introlz)** — A stepping-stone landing zone pattern that bridges the gap between startup simplicity and full enterprise architecture. Use Trey Research as the foundation while planning the eventual migration to a full Azure Landing Zone (ALZ). This pattern supports multi-subscription designs with hub/spoke networking and basic governance without the full complexity of ALZ.

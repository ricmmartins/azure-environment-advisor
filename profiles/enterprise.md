# Enterprise Profile (200+ Engineers)

## Detection Signals

| Signal | Threshold |
|--------|-----------|
| Subscriptions | 10+ |
| Total resources | 500+ |
| Regions | 2+ |
| Management groups | Full hierarchy |
| Hub/spoke networking | Present |
| Dedicated platform team | Yes |

## Philosophy

Enterprises are expected to operate at full maturity. Recommendations for this profile are **governance-focused and compliance-aware** — gaps in governance, security, or reliability at this scale represent significant organizational risk. Every finding should be tracked, prioritized, and remediated through established processes.

## What Matters Most

- **Landing zone maturity** — Full ALZ or equivalent architecture with management group hierarchy, centralized networking, and platform subscriptions.
- **RBAC governance** — PIM for privileged roles, group-based RBAC, regular access reviews.
- **Full WAF compliance** — All five pillars of the Well-Architected Framework should be assessed and addressed.
- **DR tested** — Disaster recovery plans must exist and be tested regularly (not just documented).
- **Policy enforcement** — Comprehensive Azure Policy assignments in Deny/DeployIfNotExists mode, not just Audit.

## Expectations

- **Full Azure Landing Zone (ALZ)** or equivalent architecture deployed.
- **Privileged Identity Management (PIM)** for Owner, Contributor, and sensitive roles.
- **Conditional Access** with risk-based policies, device compliance, and location-based controls.
- **Comprehensive Azure Policy** across all management group scopes.
- **Multi-region DR** with documented and tested failover procedures.
- **Centralized logging** to Log Analytics with Sentinel or equivalent SIEM.
- **IaC everywhere** — All infrastructure managed through code with CI/CD pipelines.
- Formal change management, incident response, and security operations processes.

## Severity Adjustments

All rules apply at full severity. Governance gaps that might be acceptable for smaller organizations are Critical at enterprise scale.

| Rule ID | Rule Title | Default Severity | Enterprise Severity | Rationale |
|---------|-----------|-----------------|---------------------|-----------|
| **Reliability** | | | | |
| REL-001 | Azure SQL not zone-redundant | High | High | Production databases must be zone-redundant |
| REL-002 | App Service not zone-redundant | High | High | Production workloads must be zone-redundant |
| REL-003 | Storage not using ZRS/GRS | High | Critical | Data loss risk is unacceptable |
| REL-004 | AKS not using availability zones | High | High | Container platforms must be resilient |
| REL-010 | No backup policy for Azure VMs | Critical | Critical | Non-negotiable |
| REL-011 | SQL Database no long-term retention | Medium | High | Compliance and audit requirements |
| REL-012 | No geo-replication for critical databases | High | Critical | Multi-region is expected |
| REL-013 | Blob soft delete not enabled | Medium | High | Data protection baseline |
| REL-020 | No autoscale configured for compute | High | High | Must handle demand spikes |
| REL-021 | Load balancer without health probes | High | High | Operational baseline |
| REL-022 | Single instance VM (no availability) | High | Critical | Unacceptable for production |
| REL-030 | No multi-region strategy | High | Critical | Must have multi-region DR |
| REL-031 | No documented RPO/RTO targets | Medium | High | Required for all critical workloads |
| REL-032 | Site Recovery not configured for VMs | High | High | Standard DR requirement |
| **Security** | | | | |
| SEC-001 | Defender for Cloud not enabled | Critical | Critical | Non-negotiable |
| SEC-002 | Secure Score below 50% | High | Critical | Target 80%+; below 50% is a governance failure |
| SEC-003 | Security contact not configured | Medium | High | Must have dedicated security operations |
| SEC-010 | Public database endpoints | Critical | Critical | Zero tolerance |
| SEC-011 | NSG missing on subnet | High | Critical | Network segmentation is mandatory |
| SEC-012 | Storage account allows public blob access | High | Critical | Must be disabled via policy |
| SEC-013 | No Azure Firewall or NVA for egress filtering | Medium | High | Egress filtering is expected |
| SEC-014 | Public IP addresses on VMs | Medium | High | Must justify every public IP |
| SEC-020 | RBAC uses direct user assignments | High | Critical | Group-based RBAC is mandatory |
| SEC-021 | Too many Owner/Contributor assignments | High | Critical | Must enforce least privilege via PIM |
| SEC-022 | No MFA enforcement detected | Critical | Critical | Non-negotiable; risk-based CA required |
| SEC-023 | No break-glass account pattern | Medium | Critical | Must have tested break-glass process |
| SEC-030 | No Key Vault deployed | High | Critical | Centralized secrets management required |
| SEC-031 | Key Vault using access policies instead of RBAC | Medium | High | RBAC model is the standard |
| SEC-032 | Managed identities not used | Medium | High | Must be the default auth mechanism |

## Recommended Landing Zone

**[Azure Landing Zone (ALZ)](https://aka.ms/alz)** — The full Azure Landing Zone architecture is the target for enterprise organizations. This includes management group hierarchy, platform subscriptions (connectivity, identity, management), application landing zone subscriptions, comprehensive policy assignments, and centralized networking with hub/spoke or Virtual WAN. All new workloads should be deployed into landing zone subscriptions that inherit governance from the management group hierarchy.

# Startup Profile (5–50 Engineers)

## Detection Signals

| Signal | Threshold |
|--------|-----------|
| Subscriptions | 1–2 |
| Total resources | < 50 |
| Regions | 1 |
| Management groups | None |
| Resource groups | 1–5 |

## Philosophy

Startups need to move fast without accumulating security debt. Recommendations for this profile are **pragmatic and cost-conscious** — avoid over-engineering, but build the right foundations from day one. A single subscription is perfectly fine at this stage; what matters is getting security basics right and establishing habits that will scale.

## What Matters Most

- **Security basics** — Enable Defender for Cloud, never expose database endpoints publicly, store secrets in Key Vault.
- **Budget alerts** — Set up cost alerts early; surprises kill startups.
- **Basic monitoring** — At minimum, Activity Log and resource diagnostics.
- **Secrets management** — Use Key Vault from the start; retrofitting is painful.

## Expectations

- Single subscription is acceptable.
- Basic tagging (`environment`, `owner`) is sufficient.
- **Security Defaults** for MFA enforcement (Conditional Access not required yet).
- No landing zone needed yet, but consider [Startup Scale Landing Zone (SSLZ)](https://startupscalelanding.zone) as the recommended pattern when ready to formalize.
- IaC is encouraged but not required — consistency matters more than tooling.

## Severity Adjustments

Enterprise-grade governance findings are downgraded for startups. Focus on what protects the business today.

| Rule ID | Rule Title | Default Severity | Startup Severity | Rationale |
|---------|-----------|-----------------|-----------------|-----------|
| **Reliability** | | | | |
| REL-001 | Azure SQL not zone-redundant | High | Low | Cost prohibitive; single-zone is acceptable |
| REL-002 | App Service not zone-redundant | High | Low | Cost prohibitive at this stage |
| REL-003 | Storage not using ZRS/GRS | High | Medium | LRS is fine for non-critical data; GRS for critical |
| REL-004 | AKS not using availability zones | High | Low | Most startups don't need AKS yet |
| REL-010 | No backup policy for Azure VMs | Critical | High | Backups matter, but VMs are less common |
| REL-011 | SQL Database no long-term retention | Medium | Low | Short-term retention is sufficient |
| REL-012 | No geo-replication for critical databases | High | Low | Single-region is acceptable |
| REL-013 | Blob soft delete not enabled | Medium | Medium | Easy win, keep as-is |
| REL-020 | No autoscale configured for compute | High | Low | Manual scaling is fine at low scale |
| REL-021 | Load balancer without health probes | High | Medium | Important if using LB, but many won't |
| REL-022 | Single instance VM (no availability) | High | Low | Acceptable for non-prod workloads |
| REL-030 | No multi-region strategy | High | Informational | Not expected at this stage |
| REL-031 | No documented RPO/RTO targets | Medium | Informational | Good practice but not urgent |
| REL-032 | Site Recovery not configured for VMs | High | Low | Overkill for most startups |
| **Security** | | | | |
| SEC-001 | Defender for Cloud not enabled | Critical | Critical | Non-negotiable at any size |
| SEC-002 | Secure Score below 50% | High | Medium | Aim for improvement, not perfection |
| SEC-003 | Security contact not configured | Medium | Medium | Quick setup, keep as-is |
| SEC-010 | Public database endpoints | Critical | Critical | Non-negotiable; use Private Endpoints or firewall rules |
| SEC-011 | NSG missing on subnet | High | High | Basic network hygiene |
| SEC-012 | Storage account allows public blob access | High | High | Easy to disable, high impact |
| SEC-013 | No Azure Firewall or NVA for egress filtering | Medium | Informational | Too expensive for startups |
| SEC-014 | Public IP addresses on VMs | Medium | Medium | Acceptable if NSGs are in place |
| SEC-020 | RBAC uses direct user assignments | High | Medium | Groups are better but small teams can manage |
| SEC-021 | Too many Owner/Contributor assignments | High | Medium | Small teams need broad access |
| SEC-022 | No MFA enforcement detected | Critical | Critical | Use Security Defaults at minimum |
| SEC-023 | No break-glass account pattern | Medium | Low | Important later; basic admin backup is enough |
| SEC-030 | No Key Vault deployed | High | High | Start right with secrets management |
| SEC-031 | Key Vault using access policies instead of RBAC | Medium | Low | Access policies are fine initially |
| SEC-032 | Managed identities not used | Medium | Low | Adopt when comfortable with the pattern |

## Recommended Landing Zone

**[Startup Scale Landing Zone (SSLZ)](https://startupscalelanding.zone)** — A lightweight landing zone pattern designed for startups that provides security foundations without enterprise complexity. Adopt this when the team grows beyond 10–15 engineers or when the first production workload requires formal governance.

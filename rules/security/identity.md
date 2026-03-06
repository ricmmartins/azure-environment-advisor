# Security Assessment Rules — Identity and Access

Rules for assessing RBAC hygiene, MFA enforcement, and identity security practices across the Azure environment.

---

## SEC-020 — RBAC uses direct user assignments

**Pillar:** Security
**Severity:** High
**Profiles:** High for all profiles

### What to Check
Query role assignments at the subscription scope and inspect the `principalType` field. Count assignments where `principalType` is `User` (direct) versus `Group` (group-based). A high ratio of direct user assignments indicates poor RBAC hygiene.

```kusto
authorizationresources
| where type == "microsoft.authorization/roleassignments"
| extend principalType = tostring(properties.principalType)
| summarize count() by principalType
```

Flag when direct user assignments significantly outnumber group-based assignments, or when there are more than a handful of direct user assignments.

### Finding Template
**Title:** RBAC relies on direct user assignments instead of groups
**What was found:** Found `{directCount}` direct user role assignments compared to `{groupCount}` group-based assignments at the subscription scope. Users are being granted Azure roles individually rather than through Entra ID security groups.
**Why it matters:** Direct user assignments do not scale and are error-prone. When employees change roles or leave the organization, their permissions must be individually revoked. Group-based assignments ensure consistent access control and simplify access reviews, onboarding, and offboarding.
**Recommendation:** Create Entra ID security groups that align with job functions (e.g., `sg-azure-readers`, `sg-azure-contributors`). Assign Azure roles to these groups, then add users to the appropriate groups. Remove direct user role assignments after migration.

### Learn More
- [Best practices for Azure RBAC](https://learn.microsoft.com/azure/role-based-access-control/best-practices) — recommended patterns for role assignment management
- [Learn about groups in Microsoft Entra ID](https://learn.microsoft.com/entra/fundamentals/concept-learn-about-groups) — creating and managing security groups for access control

---

## SEC-021 — Too many Owner/Contributor assignments

**Pillar:** Security
**Severity:** High
**Profiles:** High for all profiles

### What to Check
Count the number of Owner and Contributor role assignments at the subscription scope. Flag when there are more than 3 Owner assignments or more than 10 Contributor assignments.

```kusto
authorizationresources
| where type == "microsoft.authorization/roleassignments"
| extend roleId = tostring(properties.roleDefinitionId)
| where roleId endswith "8e3af657-a8ff-443c-a75c-2fe8c4bcb635" // Owner
    or roleId endswith "b24988ac-6180-42a0-ab88-20f7382dd24c" // Contributor
| extend roleName = iff(roleId endswith "8e3af657-a8ff-443c-a75c-2fe8c4bcb635", "Owner", "Contributor")
| summarize count() by roleName
```

Flag when Owner count exceeds 3 or Contributor count exceeds 10.

### Finding Template
**Title:** Excessive Owner or Contributor role assignments detected
**What was found:** Found `{ownerCount}` Owner and `{contributorCount}` Contributor role assignments at the subscription scope. This exceeds the recommended thresholds of 3 Owners and 10 Contributors.
**Why it matters:** Owner and Contributor roles grant broad permissions including the ability to create, modify, and delete any resource. Excessive privileged assignments increase the blast radius of a compromised account and violate the principle of least privilege.
**Recommendation:** Review all Owner and Contributor assignments. Replace with more specific built-in roles where possible (e.g., `Virtual Machine Contributor`, `Network Contributor`). Limit Owner to no more than 3 assignments and ensure at least 2 are assigned for redundancy.

### Learn More
- [Best practices for Azure RBAC](https://learn.microsoft.com/azure/role-based-access-control/best-practices) — guidance on limiting privileged role assignments
- [Azure built-in roles](https://learn.microsoft.com/azure/role-based-access-control/built-in-roles) — full reference of granular roles to replace broad permissions

---

## SEC-022 — No MFA enforcement detected

**Pillar:** Security
**Severity:** Critical
**Profiles:** Critical for all profiles

### What to Check
Check whether Security Defaults are enabled on the Entra ID tenant and whether Conditional Access policies exist that require MFA. If Security Defaults are disabled and no Conditional Access policies are detected, MFA is likely not enforced.

This is an inferred check — if no Conditional Access policies exist and Security Defaults are off, flag the finding. The agent cannot directly query Conditional Access policies via Resource Graph, so this relies on the absence of related configuration indicators.

### Finding Template
**Title:** No MFA enforcement detected on the tenant
**What was found:** Security Defaults are disabled on the Entra ID tenant and no Conditional Access policies were detected. Multi-factor authentication (MFA) does not appear to be enforced for user sign-ins.
**Why it matters:** MFA prevents over 99.9% of account compromise attacks. Without MFA enforcement, any user whose password is compromised through phishing, credential stuffing, or data breaches can access the Azure environment with full privileges of their assigned roles.
**Recommendation:** For organizations without Microsoft Entra ID P1/P2 licensing, enable Security Defaults immediately — this is free and enforces MFA for all users. For organizations with P1/P2, deploy Conditional Access policies that require MFA for all users accessing Azure management endpoints and for risky sign-ins.

### Learn More
- [Security defaults in Microsoft Entra ID](https://learn.microsoft.com/entra/fundamentals/security-defaults) — free baseline MFA protection for all tenants
- [Conditional Access overview](https://learn.microsoft.com/entra/identity/conditional-access/overview) — policy-based MFA and access controls for advanced scenarios

---

## SEC-023 — No break-glass account pattern

**Pillar:** Security
**Severity:** Medium
**Profiles:** Medium for scale-up and enterprise profiles, Low for startup profile

### What to Check
Look for emergency access accounts — accounts with display names containing "break-glass" or "emergency" that hold the Global Administrator role. These accounts should be cloud-only (not synced from on-premises AD) and excluded from Conditional Access policies.

```kusto
authorizationresources
| where type == "microsoft.authorization/roleassignments"
| extend principalType = tostring(properties.principalType), displayName = tostring(properties.principalName)
| where displayName contains "break-glass" or displayName contains "emergency"
```

If no matching accounts are found, flag the finding. Note that this is a heuristic check — the absence of an account with these naming patterns does not guarantee that no emergency access strategy exists, but it indicates the common pattern is not followed.

### Finding Template
**Title:** No break-glass (emergency access) account pattern detected
**What was found:** No accounts with "break-glass" or "emergency" in the display name were found with Global Administrator role assignments. The environment may lack emergency access accounts.
**Why it matters:** Break-glass accounts are critical for regaining access to the Azure/Entra tenant when normal administrative accounts are locked out due to MFA failures, Conditional Access misconfigurations, or identity provider outages. Without them, an organization can be completely locked out of its own tenant.
**Recommendation:** Create 2 cloud-only break-glass accounts with Global Administrator role. Use long, complex passwords stored securely (e.g., in a physical safe). Exclude these accounts from all Conditional Access policies. Monitor sign-in activity on these accounts with alerts for any usage.

### Learn More
- [Manage emergency access accounts in Microsoft Entra ID](https://learn.microsoft.com/entra/identity/role-based-access-control/security-emergency-access) — detailed guidance on creating, securing, and monitoring break-glass accounts

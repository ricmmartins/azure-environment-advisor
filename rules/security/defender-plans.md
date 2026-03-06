# Security Assessment Rules — Defender for Cloud

Rules for assessing Microsoft Defender for Cloud enablement, secure score health, and security contact configuration.

---

## SEC-001 — Defender for Cloud not enabled

**Pillar:** Security
**Severity:** Critical
**Profiles:** Critical for all profiles (startup, scale-up, enterprise)

### What to Check
Query `securityresources` for `microsoft.security/pricings` and inspect the `pricingTier` property on each plan. If no plans are enabled (all show `Free` or no records exist), the subscription lacks Defender coverage.

```kusto
securityresources
| where type == "microsoft.security/pricings"
| project name, properties.pricingTier
```

Look for plans such as CloudPosture, VirtualMachines, KeyVaults, Arm, Containers, and Dns. If `pricingTier` is `Free` across all plans, flag the finding.

### Finding Template
**Title:** Microsoft Defender for Cloud is not enabled
**What was found:** No Defender for Cloud plans are enabled on subscription `{subscriptionName}`. All pricing tiers are set to Free, leaving workloads without advanced threat protection.
**Why it matters:** Without Defender for Cloud, the environment has no advanced threat detection, vulnerability assessments, or security alerts. Attackers can exploit unmonitored resources without triggering any security response.
**Recommendation:** Enable Defender Cloud Security Posture Management (CSPM) which is free, then enable Defender for Servers Plan 2, Key Vault, ARM, Containers, and DNS protections based on the workloads present.

### Learn More
- [Get started with Microsoft Defender for Cloud](https://learn.microsoft.com/azure/defender-for-cloud/get-started) — initial setup and enablement steps
- [Defender for Servers introduction](https://learn.microsoft.com/azure/defender-for-cloud/defender-for-servers-introduction) — server protection capabilities and plan comparison
- [Secure score in Defender for Cloud](https://learn.microsoft.com/azure/defender-for-cloud/secure-score-security-controls) — understanding and improving your security posture

---

## SEC-002 — Secure Score below 50%

**Pillar:** Security
**Severity:** High
**Profiles:** High for all profiles

### What to Check
Query `securityresources` for `microsoft.security/securescores` and compare `properties.score.current` against `properties.score.max` to compute the percentage. A score below 50% indicates significant unaddressed security recommendations.

```kusto
securityresources
| where type == "microsoft.security/securescores"
| extend current = properties.score.current, max = properties.score.max
| extend percentage = (todouble(current) / todouble(max)) * 100
| project subscriptionId, current, max, percentage
```

Flag when the computed percentage is below 50.

### Finding Template
**Title:** Secure Score is below 50%
**What was found:** The Defender for Cloud Secure Score for subscription `{subscriptionName}` is `{current}`/`{max}` (`{percentage}%`), indicating that more than half of the security recommendations remain unaddressed.
**Why it matters:** A low Secure Score means the environment has a large attack surface with known, unmitigated security risks. Each unaddressed recommendation represents a potential entry point for attackers.
**Recommendation:** Review and address critical Defender for Cloud recommendations first, focusing on the controls that contribute the most points to the Secure Score. Prioritize recommendations in the Identity, Network, and Data categories.

### Learn More
- [Secure score in Defender for Cloud](https://learn.microsoft.com/azure/defender-for-cloud/secure-score-security-controls) — how the score is calculated and what controls contribute
- [Security recommendations reference](https://learn.microsoft.com/azure/defender-for-cloud/recommendations-reference) — full list of recommendations and remediation steps

---

## SEC-003 — Security contact not configured

**Pillar:** Security
**Severity:** Medium
**Profiles:** Medium for all profiles

### What to Check
Check whether a security contact email is configured for alert notifications. Query the security contacts configuration or check via the Defender for Cloud settings. If no email address or phone number is configured, security alerts may go unnoticed.

```kusto
securityresources
| where type == "microsoft.security/securitycontacts"
| project name, properties.emails, properties.phone, properties.alertNotifications
```

Flag when no security contact records exist or when the email field is empty.

### Finding Template
**Title:** Security contact not configured for alert notifications
**What was found:** No security contact email is configured on subscription `{subscriptionName}`. Security alerts from Defender for Cloud have no designated recipient.
**Why it matters:** Without a security contact, critical security alerts are not delivered to the appropriate personnel. Threats and incidents may go unnoticed for extended periods, increasing the blast radius of a potential breach.
**Recommendation:** Configure a security contact with a team email address (such as a security operations distribution list) and a phone number for high-severity alerts. Enable email notifications for high-severity alerts at minimum.

### Learn More
- [Configure email notifications for security alerts](https://learn.microsoft.com/azure/defender-for-cloud/configure-email-notifications) — step-by-step guide for setting up alert recipients

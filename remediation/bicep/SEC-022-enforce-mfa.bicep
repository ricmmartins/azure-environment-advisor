// ============================================================================
// Rule:        SEC-022 — No MFA enforcement detected
// Description: Enforces Multi-Factor Authentication for all users by enabling
//              Entra ID Security Defaults. For organisations with Entra ID P1/P2,
//              a Conditional Access policy is the recommended approach — see the
//              az CLI commands below because Bicep does not yet support the
//              Microsoft.Graph Conditional Access resource provider in GA.
//
// Scope:       Subscription (Security Defaults toggle) / Tenant (Conditional Access)
//
// Usage:
//   # Option 1 — Enable Security Defaults (free tier, no P1/P2 needed)
//   az rest --method PATCH \
//     --url "https://graph.microsoft.com/v1.0/policies/identitySecurityDefaultsEnforcementPolicy" \
//     --headers "Content-Type=application/json" \
//     --body '{"isEnabled": true}'
//
//   # Option 2 — Conditional Access policy via az CLI (requires Entra ID P1/P2)
//   az deployment sub create \
//     --location eastus \
//     --template-file remediation/bicep/SEC-022-enforce-mfa.bicep \
//     --parameters exclusionGroupObjectIds='["<group-object-id>"]'
//
// NOTE: Review exclusion lists carefully before deploying. Emergency/break-glass
//       accounts should always be excluded from MFA policies.
// ============================================================================

targetScope = 'subscription'

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------

@description('Display name for the Conditional Access policy.')
param policyDisplayName string = 'Require MFA for all users'

@description('Object IDs of Entra ID groups to exclude from the MFA policy (e.g. break-glass accounts).')
param exclusionGroupObjectIds array = []

@description('Set to true to enforce the policy immediately; false creates it in report-only mode.')
param enforcePolicy bool = false

// ---------------------------------------------------------------------------
// Guidance — Conditional Access via az CLI
// ---------------------------------------------------------------------------
// Bicep does not natively support Microsoft.Graph/beta Conditional Access
// resources in GA deployments. Use the az CLI commands below to create the
// policy programmatically.
//
// Step 1 — Create the policy JSON payload:
//
//   {
//     "displayName": "<policyDisplayName>",
//     "state": "<enforcePolicy ? 'enabled' : 'enabledForReportingButNotEnforced'>",
//     "conditions": {
//       "users": {
//         "includeUsers": ["All"],
//         "excludeGroups": <exclusionGroupObjectIds>
//       },
//       "applications": {
//         "includeApplications": ["All"]
//       }
//     },
//     "grantControls": {
//       "operator": "OR",
//       "builtInControls": ["mfa"]
//     }
//   }
//
// Step 2 — Deploy:
//
//   az rest --method POST \
//     --url "https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies" \
//     --headers "Content-Type=application/json" \
//     --body @policy.json
//
// Step 3 — Verify:
//
//   az rest --method GET \
//     --url "https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies"
// ---------------------------------------------------------------------------

// Placeholder resource to make the template valid and allow parameter validation.
// The actual remediation is performed via the az CLI commands above.
resource deploymentMarker 'Microsoft.Resources/tags@2024-03-01' = {
  name: 'default'
  properties: {
    tags: {
      'advisor-rule': 'SEC-022'
      'remediation': 'enforce-mfa'
      'policy-name': policyDisplayName
      'enforce': string(enforcePolicy)
    }
  }
}

output guidance string = 'SEC-022: Use the az CLI commands in the template comments to deploy a Conditional Access policy. Bicep does not support Microsoft.Graph Conditional Access resources natively.'
output exclusionGroups array = exclusionGroupObjectIds

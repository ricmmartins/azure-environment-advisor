// ============================================================================
// Rule:        SEC-003 — Security contact not configured
// Description: Configures a Microsoft Defender for Cloud security contact with
//              email and phone notifications for high-severity alerts.
//
// Scope:       Subscription
//
// Usage:
//   az deployment sub create \
//     --location eastus \
//     --template-file remediation/bicep/SEC-003-security-contact.bicep \
//     --parameters email=security-team@contoso.com \
//                  phone='+15551234567'
// ============================================================================

targetScope = 'subscription'

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------

@description('Email address for security alert notifications. Use a team distribution list.')
param email string

@description('Phone number for high-severity security alerts (E.164 format recommended).')
param phone string

@description('Minimum alert severity that triggers notifications.')
@allowed([
  'High'
  'Medium'
  'Low'
])
param alertMinSeverity string = 'High'

@description('Also notify subscription owners and contributors.')
param notifyAdmins bool = true

// ---------------------------------------------------------------------------
// Security Contact
// ---------------------------------------------------------------------------

resource securityContact 'Microsoft.Security/securityContacts@2023-12-01-preview' = {
  name: 'default'
  properties: {
    emails: email
    phone: phone
    isEnabled: true
    notificationsByRole: {
      state: notifyAdmins ? 'On' : 'Off'
      roles: [
        'Owner'
        'Contributor'
      ]
    }
    notificationsSources: [
      {
        sourceType: 'Alert'
        minimalSeverity: alertMinSeverity
      }
      {
        sourceType: 'AttackPath'
        minimalRiskLevel: 'High'
      }
    ]
  }
}

output contactId string = securityContact.id
output configuredEmail string = email

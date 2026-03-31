// ============================================================================
// Rule:        GOV-011 — No prod/non-prod separation
// Description: Creates a management group hierarchy that separates production
//              and non-production workloads, following Azure Landing Zone
//              patterns. Subscriptions can then be moved under the appropriate
//              management group.
//
// Scope:       Tenant (management groups are tenant-level resources)
//
// Usage:
//   az deployment tenant create \
//     --location eastus \
//     --template-file remediation/bicep/GOV-011-environment-separation.bicep \
//     --parameters rootMgName=mg-contoso
//
// NOTE: Requires Tenant Root Group write permissions (e.g. elevated access).
//       See: https://learn.microsoft.com/azure/role-based-access-control/elevate-access-global-admin
// ============================================================================

targetScope = 'tenant'

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------

@description('Display name (and ID prefix) for the root management group.')
param rootMgName string

@description('Display name for the production management group.')
param prodMgDisplayName string = 'Production'

@description('Display name for the non-production management group.')
param nonprodMgDisplayName string = 'Non-Production'

@description('Display name for the sandbox management group.')
param sandboxMgDisplayName string = 'Sandbox'

// ---------------------------------------------------------------------------
// Variables
// ---------------------------------------------------------------------------

var rootMgId = rootMgName
var prodMgId = '${rootMgName}-prod'
var nonprodMgId = '${rootMgName}-nonprod'
var sandboxMgId = '${rootMgName}-sandbox'

// ---------------------------------------------------------------------------
// Management Group Hierarchy
// ---------------------------------------------------------------------------

// Root management group
resource rootMg 'Microsoft.Management/managementGroups@2023-04-01' = {
  name: rootMgId
  properties: {
    displayName: rootMgName
  }
}

// Production
resource prodMg 'Microsoft.Management/managementGroups@2023-04-01' = {
  name: prodMgId
  properties: {
    displayName: prodMgDisplayName
    details: {
      parent: {
        id: rootMg.id
      }
    }
  }
}

// Non-Production
resource nonprodMg 'Microsoft.Management/managementGroups@2023-04-01' = {
  name: nonprodMgId
  properties: {
    displayName: nonprodMgDisplayName
    details: {
      parent: {
        id: rootMg.id
      }
    }
  }
}

// Sandbox
resource sandboxMg 'Microsoft.Management/managementGroups@2023-04-01' = {
  name: sandboxMgId
  properties: {
    displayName: sandboxMgDisplayName
    details: {
      parent: {
        id: rootMg.id
      }
    }
  }
}

output rootMgId string = rootMg.id
output prodMgId string = prodMg.id
output nonprodMgId string = nonprodMg.id
output sandboxMgId string = sandboxMg.id
output hierarchy string = '${rootMgName} → [${prodMgDisplayName}, ${nonprodMgDisplayName}, ${sandboxMgDisplayName}]'

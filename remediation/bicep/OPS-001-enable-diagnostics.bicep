// ============================================================================
// Rule:        OPS-001 — No diagnostic settings configured
// Description: Creates a Log Analytics workspace and configures subscription-
//              level diagnostic settings to forward all Activity Log categories.
//
// Scope:       Subscription
//
// Usage:
//   az deployment sub create \
//     --location eastus \
//     --template-file remediation/bicep/OPS-001-enable-diagnostics.bicep \
//     --parameters workspaceName=law-diagnostics \
//                  location=eastus \
//                  retentionDays=90
// ============================================================================

targetScope = 'subscription'

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------

@description('Name of the Log Analytics workspace to create.')
param workspaceName string

@description('Azure region for the Log Analytics workspace.')
param location string

@description('Number of days to retain logs in the workspace.')
@minValue(30)
@maxValue(730)
param retentionDays int = 90

@description('Resource group to hold the Log Analytics workspace. Created if it does not exist.')
param resourceGroupName string = 'rg-diagnostics'

@description('Name for the subscription-level diagnostic setting.')
param diagnosticSettingName string = 'activity-log-to-law'

// ---------------------------------------------------------------------------
// Resource Group
// ---------------------------------------------------------------------------

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
}

// ---------------------------------------------------------------------------
// Log Analytics Workspace (deployed into resource group via module)
// ---------------------------------------------------------------------------

module workspace 'law-module.bicep' = {
  name: 'deploy-law'
  scope: rg
  params: {
    workspaceName: workspaceName
    location: location
    retentionDays: retentionDays
  }
}

// ---------------------------------------------------------------------------
// Subscription Diagnostic Setting — forward all Activity Log categories
// ---------------------------------------------------------------------------

resource diagnosticSetting 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: diagnosticSettingName
  properties: {
    workspaceId: workspace.outputs.workspaceId
    logs: [
      {
        category: 'Administrative'
        enabled: true
      }
      {
        category: 'Security'
        enabled: true
      }
      {
        category: 'ServiceHealth'
        enabled: true
      }
      {
        category: 'Alert'
        enabled: true
      }
      {
        category: 'Recommendation'
        enabled: true
      }
      {
        category: 'Policy'
        enabled: true
      }
      {
        category: 'Autoscale'
        enabled: true
      }
      {
        category: 'ResourceHealth'
        enabled: true
      }
    ]
  }
}

output workspaceId string = workspace.outputs.workspaceId
output diagnosticSettingId string = diagnosticSetting.id

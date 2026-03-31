// ============================================================================
// Module:      Log Analytics Workspace
// Description: Deploys a Log Analytics workspace. Used by OPS-001 and other
//              templates that need a workspace scoped to a resource group.
// ============================================================================

targetScope = 'resourceGroup'

@description('Name of the Log Analytics workspace.')
param workspaceName string

@description('Azure region for the workspace.')
param location string = resourceGroup().location

@description('Number of days to retain data.')
@minValue(30)
@maxValue(730)
param retentionDays int = 90

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: workspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: retentionDays
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

output workspaceId string = workspace.id
output workspaceName string = workspace.name

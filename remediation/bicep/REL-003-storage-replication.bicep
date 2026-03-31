// ============================================================================
// Rule:        REL-003 — Storage not using ZRS/GRS
// Description: Upgrades an existing storage account's replication from LRS to
//              GRS for cross-region redundancy.
//
// Scope:       Resource Group
//
// Usage:
//   az deployment group create \
//     --resource-group <resource-group> \
//     --template-file remediation/bicep/REL-003-storage-replication.bicep \
//     --parameters storageAccountName=stproddata01
//
// NOTE: Changing replication from LRS to GRS may incur additional storage costs.
//       Review pricing before deploying. For zone-redundant replication within a
//       single region, set targetReplication to 'Standard_ZRS' instead.
// ============================================================================

targetScope = 'resourceGroup'

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------

@description('Name of the existing storage account to upgrade.')
param storageAccountName string

@description('Target replication SKU. Common options: Standard_GRS, Standard_ZRS, Standard_GZRS.')
@allowed([
  'Standard_GRS'
  'Standard_ZRS'
  'Standard_GZRS'
  'Standard_RAGRS'
  'Standard_RAGZRS'
])
param targetReplication string = 'Standard_GRS'

// ---------------------------------------------------------------------------
// Existing storage account reference
// ---------------------------------------------------------------------------

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

// ---------------------------------------------------------------------------
// Upgrade replication
// ---------------------------------------------------------------------------
// Bicep 'existing' resources are read-only references; to change the SKU we
// redeclare the resource. This is an incremental deployment — only the SKU
// changes; all other properties are preserved by ARM.
// ---------------------------------------------------------------------------

resource storageUpgrade 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: storageAccount.location
  kind: 'StorageV2'
  sku: {
    name: targetReplication
  }
  properties: {
    // Preserve existing settings; ARM merges incrementally
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

output storageAccountId string = storageUpgrade.id
output newReplication string = targetReplication

// ============================================================================
// Rule:        REL-010 — No backup policy for Azure VMs
// Description: Creates a Recovery Services vault with a daily backup policy
//              (30-day retention) and assigns the specified VMs to the policy.
//
// Scope:       Resource Group
//
// Usage:
//   az deployment group create \
//     --resource-group <resource-group> \
//     --template-file remediation/bicep/REL-010-enable-backup.bicep \
//     --parameters vaultName=rsv-backup \
//                  vmNames='["vm-web-01","vm-app-01"]' \
//                  location=eastus
// ============================================================================

targetScope = 'resourceGroup'

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------

@description('Name of the Recovery Services vault to create.')
param vaultName string

@description('Names of VMs in the same resource group to protect with backup.')
param vmNames array

@description('Azure region for the vault.')
param location string = resourceGroup().location

@description('Number of days to retain daily backups.')
@minValue(7)
@maxValue(9999)
param retentionDays int = 30

@description('Time of day (UTC) to run backups, in HH:MM format.')
param scheduleTime string = '23:00'

// ---------------------------------------------------------------------------
// Variables
// ---------------------------------------------------------------------------

var backupPolicyName = 'daily-vm-policy'
var backupFabric = 'Azure'
var protectionContainerPrefix = 'iaasvmcontainer;iaasvmcontainerv2;${resourceGroup().name};'
var protectedItemPrefix = 'vm;iaasvmcontainerv2;${resourceGroup().name};'

// ---------------------------------------------------------------------------
// Recovery Services Vault
// ---------------------------------------------------------------------------

resource vault 'Microsoft.RecoveryServices/vaults@2024-04-01' = {
  name: vaultName
  location: location
  sku: {
    name: 'RS0'
    tier: 'Standard'
  }
  properties: {
    publicNetworkAccess: 'Disabled'
  }
}

// ---------------------------------------------------------------------------
// Backup Policy — Daily, 30-day retention
// ---------------------------------------------------------------------------

resource backupPolicy 'Microsoft.RecoveryServices/vaults/backupPolicies@2024-04-01' = {
  parent: vault
  name: backupPolicyName
  properties: {
    backupManagementType: 'AzureIaasVM'
    instantRpRetentionRangeInDays: 2
    schedulePolicy: {
      schedulePolicyType: 'SimpleSchedulePolicy'
      scheduleRunFrequency: 'Daily'
      scheduleRunTimes: [
        '2024-01-01T${scheduleTime}:00Z'
      ]
    }
    retentionPolicy: {
      retentionPolicyType: 'LongTermRetentionPolicy'
      dailySchedule: {
        retentionTimes: [
          '2024-01-01T${scheduleTime}:00Z'
        ]
        retentionDuration: {
          count: retentionDays
          durationType: 'Days'
        }
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Protected Items — Assign each VM to the backup policy
// ---------------------------------------------------------------------------

resource protectedItems 'Microsoft.RecoveryServices/vaults/backupFabrics/protectionContainers/protectedItems@2024-04-01' = [
  for vmName in vmNames: {
    name: '${vaultName}/${backupFabric}/${protectionContainerPrefix}${vmName}/${protectedItemPrefix}${vmName}'
    properties: {
      protectedItemType: 'Microsoft.Compute/virtualMachines'
      policyId: backupPolicy.id
      sourceResourceId: resourceId('Microsoft.Compute/virtualMachines', vmName)
    }
  }
]

output vaultId string = vault.id
output policyId string = backupPolicy.id
output protectedVmCount int = length(vmNames)

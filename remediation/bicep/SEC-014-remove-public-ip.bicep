// ============================================================================
// Rule:        SEC-014 — Public IP addresses on VMs
// Description: Adds a high-priority NSG deny rule to block all inbound traffic
//              from the Internet, mitigating exposure until the public IP can be
//              removed and replaced with Azure Bastion or a load balancer.
//
// Scope:       Resource Group
//
// Usage:
//   az deployment group create \
//     --resource-group <resource-group> \
//     --template-file remediation/bicep/SEC-014-remove-public-ip.bicep \
//     --parameters nsgName=<nsg-name>
// ============================================================================

targetScope = 'resourceGroup'

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------

@description('Name of the existing Network Security Group to update.')
param nsgName string

@description('Priority for the deny rule. Must not conflict with existing rules.')
@minValue(100)
@maxValue(4096)
param rulePriority int = 100

@description('Name of the deny rule to create.')
param ruleName string = 'DenyAllInboundFromInternet'

// ---------------------------------------------------------------------------
// Existing NSG reference
// ---------------------------------------------------------------------------

resource nsg 'Microsoft.Network/networkSecurityGroups@2024-01-01' existing = {
  name: nsgName
}

// ---------------------------------------------------------------------------
// Deny inbound from Internet
// ---------------------------------------------------------------------------

resource denyInternetInbound 'Microsoft.Network/networkSecurityGroups/securityRules@2024-01-01' = {
  parent: nsg
  name: ruleName
  properties: {
    priority: rulePriority
    direction: 'Inbound'
    access: 'Deny'
    protocol: '*'
    sourcePortRange: '*'
    destinationPortRange: '*'
    sourceAddressPrefix: 'Internet'
    destinationAddressPrefix: '*'
    description: 'SEC-014: Deny all inbound traffic from the Internet. Remove public IPs and use Azure Bastion or a load balancer instead.'
  }
}

output ruleId string = denyInternetInbound.id
output message string = 'SEC-014: Deny-all-inbound rule added to NSG ${nsgName}. Next step: remove public IPs from VMs and switch to Azure Bastion.'

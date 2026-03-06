# Security Assessment Rules — Network Security

Rules for assessing network isolation, access controls, and egress filtering across the Azure environment.

---

## SEC-010 — Public database endpoints

**Pillar:** Security
**Severity:** Critical
**Profiles:** Critical for scale-up and enterprise profiles, High for startup profile

### What to Check
Query for SQL Servers, PostgreSQL Flexible Servers, MySQL Flexible Servers, and Cosmos DB accounts that have `publicNetworkAccess` set to `Enabled` and do not have an associated Private Endpoint connection.

```kusto
resources
| where type in (
    "microsoft.sql/servers",
    "microsoft.dbforpostgresql/flexibleservers",
    "microsoft.dbformysql/flexibleservers",
    "microsoft.documentdb/databaseaccounts"
  )
| where properties.publicNetworkAccess =~ "Enabled"
| project name, type, resourceGroup, subscriptionId, publicAccess = properties.publicNetworkAccess
```

Cross-reference with Private Endpoint connections to confirm whether any private connectivity exists. Databases with public access enabled and no Private Endpoint are flagged.

### Finding Template
**Title:** Database has public endpoint enabled with no Private Endpoint
**What was found:** `{resourceType}` resource `{resourceName}` in resource group `{resourceGroup}` has `publicNetworkAccess` set to Enabled and has no associated Private Endpoint connection. The database is accessible from the public internet.
**Why it matters:** Public database endpoints expose sensitive data stores directly to the internet, making them targets for brute-force attacks, SQL injection, and credential stuffing. Even with firewall rules, a misconfiguration can expose the entire dataset.
**Recommendation:** Deploy a Private Endpoint for each database in the appropriate VNet subnet. After verifying connectivity through the Private Endpoint, disable public network access on the database resource.

### Learn More
- [What is Azure Private Endpoint?](https://learn.microsoft.com/azure/private-link/private-endpoint-overview) — overview of Private Endpoint architecture and use cases
- [What is Azure Private Link?](https://learn.microsoft.com/azure/private-link/private-link-overview) — understanding the Private Link service and supported resources

---

## SEC-011 — NSG missing on subnet

**Pillar:** Security
**Severity:** High
**Profiles:** High for all profiles

### What to Check
Query virtual networks and inspect each subnet for an associated Network Security Group. Exclude special-purpose subnets that do not support or require NSGs: `AzureBastionSubnet`, `GatewaySubnet`, and `AzureFirewallSubnet`.

```kusto
resources
| where type == "microsoft.network/virtualnetworks"
| mv-expand subnet = properties.subnets
| where subnet.name !in ("AzureBastionSubnet", "GatewaySubnet", "AzureFirewallSubnet")
| where isnull(subnet.properties.networkSecurityGroup)
| project vnetName = name, subnetName = tostring(subnet.name), resourceGroup, subscriptionId
```

Flag any non-exempt subnet that has no NSG association.

### Finding Template
**Title:** Subnet has no Network Security Group associated
**What was found:** Subnet `{subnetName}` in VNet `{vnetName}` (resource group `{resourceGroup}`) does not have a Network Security Group (NSG) associated. All inbound and outbound traffic is implicitly allowed.
**Why it matters:** Without an NSG, there are no network-level access controls on the subnet. Any resource deployed into this subnet accepts all traffic by default, which can allow lateral movement within the network or unauthorized access from other subnets.
**Recommendation:** Create a Network Security Group with a deny-all-inbound default rule. Add explicit allow rules only for required traffic flows, then associate the NSG with the subnet.

### Learn More
- [Network security groups overview](https://learn.microsoft.com/azure/virtual-network/network-security-groups-overview) — how NSGs work and rule evaluation order
- [Create and manage network security groups](https://learn.microsoft.com/azure/virtual-network/manage-network-security-group) — step-by-step guide for NSG creation and association

---

## SEC-012 — Storage account allows public blob access

**Pillar:** Security
**Severity:** High
**Profiles:** High for all profiles

### What to Check
Query storage accounts and check the `allowBlobPublicAccess` property. When set to `true`, individual containers can be configured for anonymous public read access.

```kusto
resources
| where type == "microsoft.storage/storageaccounts"
| where properties.allowBlobPublicAccess == true
| project name, resourceGroup, subscriptionId, kind, properties.allowBlobPublicAccess
```

Flag any storage account where `allowBlobPublicAccess` is `true`.

### Finding Template
**Title:** Storage account allows public blob access
**What was found:** Storage account `{storageAccountName}` in resource group `{resourceGroup}` has `allowBlobPublicAccess` set to `true`. Individual containers may be configured for anonymous public read access.
**Why it matters:** Allowing public blob access means any container in the storage account can be set to allow anonymous reads. This has led to numerous data breaches where sensitive files were unintentionally exposed. Even if no containers are currently public, the setting leaves the door open for accidental exposure.
**Recommendation:** Disable public blob access on the storage account unless it is explicitly required for static website hosting. Set `allowBlobPublicAccess` to `false` at the storage account level to prevent any container from being made public.

### Learn More
- [Prevent anonymous public read access to containers and blobs](https://learn.microsoft.com/azure/storage/blobs/anonymous-read-access-prevent) — how to disable and audit public access
- [Manage access to Azure Storage resources](https://learn.microsoft.com/azure/storage/blobs/storage-manage-access-to-resources) — authentication and authorization options

---

## SEC-013 — No Azure Firewall or NVA for egress filtering

**Pillar:** Security
**Severity:** Medium
**Profiles:** Medium for scale-up profile, Low for startup profile, High for enterprise profile

### What to Check
Query for the presence of Azure Firewall resources or third-party Network Virtual Appliances (NVAs) in hub VNets. If no firewall or NVA exists, outbound traffic from the environment is unfiltered.

```kusto
resources
| where type == "microsoft.network/azurefirewalls"
| project name, resourceGroup, subscriptionId
```

Also check for NVA indicators such as VMs in a hub VNet with IP forwarding enabled. If neither Azure Firewall nor an NVA is found, flag the finding.

### Finding Template
**Title:** No centralized egress filtering detected
**What was found:** No Azure Firewall or third-party Network Virtual Appliance (NVA) was found in the environment. Outbound internet traffic from workloads is not centrally filtered or inspected.
**Why it matters:** Without egress filtering, compromised workloads can freely communicate with command-and-control servers, exfiltrate data, or download additional malware. Egress filtering is a critical defense-in-depth control for detecting and blocking post-compromise activity.
**Recommendation:** Deploy Azure Firewall in a hub VNet for centralized egress control. Configure application rules and network rules to allow only required outbound destinations. Route all workload subnets through the firewall using User Defined Routes (UDRs).

### Learn More
- [What is Azure Firewall?](https://learn.microsoft.com/azure/firewall/overview) — overview of Azure Firewall features and SKUs
- [Deploy and configure Azure Firewall](https://learn.microsoft.com/azure/firewall/tutorial-firewall-deploy-portal) — step-by-step deployment tutorial

---

## SEC-014 — Public IP addresses on VMs

**Pillar:** Security
**Severity:** Medium
**Profiles:** Medium for all profiles

### What to Check
Query for virtual machines that have a public IP address directly associated with their network interface.

```kusto
resources
| where type == "microsoft.network/networkinterfaces"
| mv-expand ipConfig = properties.ipConfigurations
| where isnotnull(ipConfig.properties.publicIPAddress)
| project nicName = name, resourceGroup, subscriptionId, publicIpId = tostring(ipConfig.properties.publicIPAddress.id)
```

Cross-reference the NIC owner to identify the associated VM. Flag any VM that has a directly attached public IP.

### Finding Template
**Title:** Virtual machine has a public IP address directly attached
**What was found:** VM `{vmName}` in resource group `{resourceGroup}` has a public IP address (`{publicIpAddress}`) directly associated with its network interface. The VM is reachable from the internet.
**Why it matters:** Public IPs on VMs expose management ports (RDP 3389, SSH 22) and application ports directly to the internet. This is the most common attack vector for VM compromise, enabling brute-force attacks and exploitation of unpatched services.
**Recommendation:** Remove the public IP address from the VM. Use Azure Bastion for secure RDP/SSH management access, or connect via a VPN or ExpressRoute gateway. If the VM hosts a public-facing application, place it behind a Load Balancer or Application Gateway instead.

### Learn More
- [Azure Bastion overview](https://learn.microsoft.com/azure/bastion/bastion-overview) — secure RDP/SSH access without public IPs
- [Public IP addresses in Azure](https://learn.microsoft.com/azure/virtual-network/ip-services/public-ip-addresses) — when and how to use public IPs securely

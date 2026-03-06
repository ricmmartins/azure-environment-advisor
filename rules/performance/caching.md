# Performance Assessment Rules — Caching

Rules for assessing whether appropriate caching layers are in place to improve application performance and reduce backend load.

---

## PERF-010 — No caching layer detected

**Pillar:** Performance  
**Severity:** Medium  
**Profiles:** startup: Low, scale-up: Medium, enterprise: Medium

### What to Check
Query the subscription for Azure Cache for Redis, Azure CDN, or Azure Front Door resources. If none are found, the environment has no managed caching layer.

```kusto
resources
| where type in~ (
    "microsoft.cache/redis",
    "microsoft.cache/redisenterprise",
    "microsoft.cdn/profiles",
    "microsoft.network/frontdoors",
    "microsoft.cdn/profiles/afdendpoints"
  )
| summarize count() by type
```

If the query returns zero results, this finding applies.

### Finding Template
**Title:** No caching layer detected in the environment  
**What was found:** No Azure Cache for Redis, Azure CDN, or Azure Front Door resources were found in subscription `{subscriptionId}`.  
**Why it matters:** Without a caching layer, every request hits the backend or origin directly. This increases latency for end users, raises compute costs, and limits the ability to absorb traffic spikes gracefully.  
**Recommendation:** Add Azure Cache for Redis for session state and frequently accessed data caching. Deploy Azure CDN or Azure Front Door for static asset acceleration and edge caching.

### Learn More
- [Azure Cache for Redis overview](https://learn.microsoft.com/azure/azure-cache-for-redis/cache-overview) — Managed in-memory data store for caching, session management, and real-time analytics
- [Azure CDN overview](https://learn.microsoft.com/azure/cdn/cdn-overview) — Global content delivery network for static content acceleration

---

## PERF-011 — CDN not configured for static assets

**Pillar:** Performance  
**Severity:** Low  
**Profiles:** startup: Low, scale-up: Low, enterprise: Low

### What to Check
Identify App Service apps or Storage Accounts with static website hosting enabled that do not have an Azure CDN or Azure Front Door endpoint in front of them. Cross-reference web app hostnames and storage static website endpoints against CDN/Front Door origin configurations.

```kusto
resources
| where type == "microsoft.web/sites"
    or (type == "microsoft.storage/storageaccounts"
        and properties.primaryEndpoints.web != "")
| project name, type, resourceGroup, subscriptionId
```

Then verify whether any CDN or Front Door origins reference these resources:

```kusto
resources
| where type in~ ("microsoft.cdn/profiles/endpoints", "microsoft.cdn/profiles/afdendpoints")
| mv-expand origin = properties.origins
| project endpointName = name, originHostName = tostring(origin.properties.hostName)
```

If the web app or storage account hostname does not appear as a CDN/Front Door origin, this finding applies.

### Finding Template
**Title:** Static assets served without CDN  
**What was found:** Resource `{name}` (`{type}`) in resource group `{resourceGroup}` serves content directly to users without a CDN or Front Door in front.  
**Why it matters:** Serving static assets directly from the origin increases latency for geographically distributed users and puts unnecessary load on the origin server. CDN edge caching can reduce origin requests by 60–90%.  
**Recommendation:** Deploy Azure CDN or Azure Front Door with the resource as the origin. Configure caching rules for static file extensions (.js, .css, .png, .woff2).

### Learn More
- [Azure CDN overview](https://learn.microsoft.com/azure/cdn/cdn-overview) — Content delivery network for caching static content at edge locations
- [What is Azure Front Door?](https://learn.microsoft.com/azure/frontdoor/front-door-overview) — Global load balancer and CDN with WAF, SSL offloading, and intelligent routing

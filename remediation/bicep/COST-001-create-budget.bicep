// ============================================================================
// Rule:        COST-001 — No budget alerts configured
// Description: Creates a monthly consumption budget on the subscription with
//              alert thresholds for actual and forecasted spend.
//
// Scope:       Subscription
//
// Usage:
//   az deployment sub create \
//     --location eastus \
//     --template-file remediation/bicep/COST-001-create-budget.bicep \
//     --parameters budgetName=budget-monthly \
//                  amount=5000 \
//                  contactEmails='["finance@contoso.com","devops@contoso.com"]' \
//                  thresholds='[50,80,100]'
// ============================================================================

targetScope = 'subscription'

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------

@description('Name of the budget to create.')
param budgetName string

@description('Monthly budget amount in the subscription currency.')
@minValue(1)
param amount int

@description('Email addresses to receive budget alert notifications.')
param contactEmails array

@description('Array of percentage thresholds for actual-spend alerts (e.g. [50, 80, 100]).')
param thresholds array = [
  50
  80
  100
]

@description('Percentage threshold for the forecasted-spend alert.')
param forecastThreshold int = 100

@description('Start date for the budget period (first day of a month, yyyy-MM-dd). Defaults to the first of the current month.')
param startDate string = '${utcNow('yyyy-MM')}-01'

// ---------------------------------------------------------------------------
// Variables
// ---------------------------------------------------------------------------

// Build notification objects for each actual-spend threshold
var actualNotifications = [
  for (threshold, i) in thresholds: {
    key: 'Actual_${threshold}pct'
    value: {
      enabled: true
      operator: 'GreaterThan'
      threshold: threshold
      thresholdType: 'Actual'
      contactEmails: contactEmails
      contactRoles: [
        'Owner'
        'Contributor'
      ]
    }
  }
]

var forecastNotification = {
  key: 'Forecast_${forecastThreshold}pct'
  value: {
    enabled: true
    operator: 'GreaterThan'
    threshold: forecastThreshold
    thresholdType: 'Forecasted'
    contactEmails: contactEmails
    contactRoles: [
      'Owner'
      'Contributor'
    ]
  }
}

// Merge all notifications into a single object
var allNotificationEntries = concat(actualNotifications, [forecastNotification])
var notifications = toObject(allNotificationEntries, entry => entry.key, entry => entry.value)

// ---------------------------------------------------------------------------
// Budget
// ---------------------------------------------------------------------------

resource budget 'Microsoft.Consumption/budgets@2023-11-01' = {
  name: budgetName
  properties: {
    category: 'Cost'
    amount: amount
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: startDate
    }
    notifications: notifications
  }
}

output budgetId string = budget.id
output configuredThresholds array = thresholds
output forecastThresholdPct int = forecastThreshold

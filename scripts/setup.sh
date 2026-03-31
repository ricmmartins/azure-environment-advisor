#!/usr/bin/env bash
# Azure Environment Advisor — Quick Setup
# Creates .vscode/mcp.json with your Azure subscription ID

set -e

echo ""
echo "Azure Environment Advisor — Setup"
echo "──────────────────────────────────"
echo ""

# Check prerequisites
command -v az >/dev/null 2>&1 || { echo "❌ Azure CLI not found. Install: https://docs.microsoft.com/cli/azure/install-azure-cli"; exit 1; }
command -v code >/dev/null 2>&1 || echo "⚠️  VS Code CLI not found (optional). Install: https://code.visualstudio.com/"

# Check Azure login
if ! az account show >/dev/null 2>&1; then
    echo "🔐 Not logged into Azure. Opening browser..."
    az login
fi

echo ""
echo "Your Azure subscriptions:"
echo ""
az account list --query "[].{Name:name, Id:id, State:state}" -o table
echo ""

# Get subscription ID
CURRENT_SUB=$(az account show --query "id" -o tsv 2>/dev/null || true)
if [ -n "$CURRENT_SUB" ]; then
    CURRENT_NAME=$(az account show --query "name" -o tsv 2>/dev/null || true)
    echo "Current subscription: $CURRENT_NAME ($CURRENT_SUB)"
    read -p "Use this subscription? (Y/n): " USE_CURRENT
    if [ "$USE_CURRENT" = "n" ] || [ "$USE_CURRENT" = "N" ]; then
        read -p "Enter subscription ID: " SUB_ID
    else
        SUB_ID="$CURRENT_SUB"
    fi
else
    read -p "Enter subscription ID: " SUB_ID
fi

if [ -z "$SUB_ID" ]; then
    echo "❌ No subscription ID provided."
    exit 1
fi

# Create .vscode/mcp.json
mkdir -p .vscode
cat > .vscode/mcp.json <<EOF
{
  "servers": {
    "azure-mcp-server": {
      "command": "npx",
      "args": ["-y", "@azure/mcp@latest", "server", "start"],
      "env": {
        "AZURE_SUBSCRIPTION_ID": "$SUB_ID"
      }
    }
  }
}
EOF

echo ""
echo "✅ Created .vscode/mcp.json with subscription: $SUB_ID"
echo ""
echo "Next steps:"
echo "  1. Open this folder in VS Code: code ."
echo "  2. Switch Copilot Chat to Agent mode"
echo "  3. Type: Assess my Azure subscription"
echo ""

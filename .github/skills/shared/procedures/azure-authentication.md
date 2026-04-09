# Azure Authentication Check

Canonical procedure for verifying Azure session before any Azure operations. Referenced by all skills that interact with Azure.

---

## Procedure

1. **Verify session**: Run `az account show` or `Get-AzContext` in the terminal, OR attempt a lightweight Azure MCP call (e.g., list subscriptions)

2. **If authenticated**:
   - Display the active subscription name and ID
   - Proceed to the next step

3. **If NOT authenticated**:
   - Present this message:

   ```
   ## Azure Authentication Required

   You need an active Azure session.

   **Option A — Azure CLI:**
   az login

   **Option B — Azure PowerShell:**
   Connect-AzAccount

   After authenticating, run this skill again.
   ```

   - **HARD GATE** — Stop execution. Do not proceed without authentication.

## Notes

- The Azure MCP Server operates in **read-only mode**. It cannot create, modify, or delete any Azure resource.
- Skills in this project only require **Reader** access on the target subscription(s).
- If the user specifies a subscription ID, set it as the active subscription: `az account set --subscription <id>`

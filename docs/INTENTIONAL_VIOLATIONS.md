# THN CLI — Intentional Structural Violations

## commands_sync_delta

### Invariant Violated
Sync and Delta CLI domains must remain structurally separate.

### Current State
The module `commands_sync_delta` intentionally combines Sync and Delta
responsibilities.

### Rationale
This module exists to preserve backward compatibility and staged migration
while Sync V2 and Delta inspection plumbing are stabilized.

### Scope
- Developer-only tooling
- No runtime mutation
- No user-facing contract guarantees

### Exit Strategy
This violation will be removed once:
- Delta inspection commands are fully decoupled from Sync execution
- Compatibility shims are no longer required

### Tracking
Guarded by:
- `scripts/verify_cli_domain_separation.py`

This violation is **explicit**, **temporary**, and **documented**.

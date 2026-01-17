# THN Recovery Authority and Invariants

## Status

LOCKED — Declarative Authority Reference  
No runtime behavior. No activation semantics.

---

## Purpose

This document defines the **authority boundaries, invariants, and explicit non-goals**
for *recovery-related concepts* within the THN CLI ecosystem.

It exists to:

- Prevent accidental introduction of implicit recovery behavior
- Clearly separate **execution rollback** from **post-execution recovery**
- Declare what recovery *is not* before any recovery tooling exists
- Establish a stable reference point for future recovery design work

This document **does not introduce recovery behavior**.

---

## Scope

This document governs:

- Conceptual recovery authority
- Post-failure analysis and inspection boundaries
- Historical integrity guarantees
- Relationships between recovery, diagnostics, rollback, and observability

It explicitly applies to:

- Sync V2 execution outcomes
- CDC rollback semantics (by exclusion)
- TXLOG and Status DB interpretation
- Unified history read surfaces
- Diagnostic strict-mode and policy surfaces (by exclusion)

---

## Definitions

### Rollback

Rollback is an **execution-time safety mechanism**.

Rollback:
- Occurs during an active apply operation
- Is engine-controlled
- Is scoped to declared mutation paths
- Is deterministic and stage-aware
- Exists solely to preserve filesystem safety

Rollback **is not recovery**.

---

### Recovery

Recovery refers to **post-execution analysis or remediation** of a system
after an operation has failed, partially completed, or left behind ambiguous state.

Recovery:
- Occurs *after* execution has ended
- Must never be implicit
- Must never infer missing history
- Must never reinterpret diagnostics
- Must never mutate state without explicit user intent

No recovery system currently exists in THN.

---

## Core Invariants (Non-Negotiable)

### 1. Rollback Is Not Recovery

- Rollback semantics are fully contained within execution
- Recovery must never reuse rollback mechanisms implicitly
- Recovery must never be triggered by rollback failure
- No rollback artifact implies recoverability

---

### 2. No Implicit Recovery

THN forbids recovery that activates via:

- Diagnostic output
- Missing TXLOG entries
- Status DB gaps
- CLI flags alone
- Environment variables
- Default configuration
- Version changes
- Consumer interpretation

Any recovery behavior must be:
- Explicit
- User-initiated
- Versioned (i.e., the recovery ruleset is named, immutable, and declared up front)
- Auditable

---

### 3. No History Repair or Reconstruction

Recovery systems must **never**:

- Repair TXLOG
- Synthesize missing TXLOG records
- Infer execution success or failure
- Reconcile TXLOG with Status DB
- Rewrite historical observability artifacts

Absence of history is authoritative.

---

### 4. Diagnostics Never Trigger Recovery

Diagnostics may:

- Describe state
- Annotate anomalies
- Highlight inconsistencies

Diagnostics may **never**:

- Initiate recovery
- Suggest automatic repair
- Modify recovery scope
- Alter execution records
- Influence persistence

This includes strict mode, downgrade policy, and escalation declarations.

---

### 5. Status DB Remains Authoritative

- Status DB records terminal success only
- Failed executions are intentionally excluded
- Recovery must not reinterpret Status DB contents
- Recovery must not backfill Status DB

Status DB authority is absolute and final.

---

### 6. TXLOG Remains Diagnostic Only

- TXLOG may be incomplete
- TXLOG may be missing
- TXLOG must never be repaired
- TXLOG must never be inferred

Recovery tooling must treat TXLOG as **best-effort observational data only**.

---

## Explicit Non-Goals

This document explicitly does **not**:

- Define a recovery workflow
- Introduce recovery commands
- Define recovery data structures
- Permit automatic repair
- Allow partial re-execution
- Enable rollback replay
- Introduce “resume” semantics
- Provide migration or reconciliation logic

Absence of recovery tooling is intentional.

---

## Relationship to Existing Systems

### Sync V2 Apply
- Execution-only
- Rollback-aware
- Recovery-agnostic

### CDC Rollback
- Stage-scoped
- Path-limited
- Execution-local
- Not reusable for recovery

### Diagnostics (DX-1.x / DX-2.x)
- Observational only
- No authority
- No activation semantics

### Unified History
- Read-only
- Non-inferential
- No reconciliation
- No repair

---

## Future Recovery Design (Reserved)

If recovery is introduced in a future phase, it MUST:

- Be explicitly versioned
- Be opt-in
- Declare scope and authority
- Preserve all existing invariants
- Never reinterpret historical artifacts
- Never activate implicitly
- Never alter execution records

Any such system requires a **new major design phase**.

---

## Change Policy

Any modification to this document requires:

- Explicit acknowledgment
- Documentation update
- Changelog entry
- Review of all affected authority boundaries

Silent changes are prohibited.

---

## Summary

Recovery is **undefined by design**.

This document ensures that:
- Rollback remains execution-only
- Diagnostics remain observational
- History remains immutable
- Future recovery cannot appear accidentally

The absence of recovery behavior is the guarantee.

---

End of document.

# THN Recovery Introspection Surface Index

## Status

LOCKED — Reference Index Only  
Read-only. Declarative. No activation semantics.

---

## Verification Note

This index was verified against a repository-wide audit of recovery-, rollback-,
diagnostic-, and observability-adjacent code and documentation as of commit
`d67fed1abfb1fa31d122be871aa4134b0fce9d00`.

No recovery-capable execution paths, replay engines, or implicit repair
mechanisms were found.

Any future discovery of an unlisted recovery surface is considered a defect.

---

## Purpose

This document enumerates **every surface where recovery behavior could
theoretically appear within the THN CLI ecosystem**, and explicitly classifies:

- What each surface is
- Where it lives
- Whether it is implemented, declared, or forbidden
- What authority it may have
- What it is explicitly prohibited from doing

This index exists to:

- Prevent accidental or implicit recovery behavior
- Make recovery-related surfaces auditable
- Eliminate ambiguity between rollback, recovery, and diagnostics
- Serve as the **single authoritative index** for recovery-related design space

This document **does not define recovery behavior**.  
It defines **where recovery must not occur** and **where it may be declared in the future**.

---

## Relationship to Other Documents

This index is constrained by:

- `THN_CLI_DX2_Invariants.md`
- `DX-2.x Diagnostics Policy and Invariants`
- `diagnostics/diagnostics_consumer_contracts.md`
- `THN_CLI_Contract_Boundaries.md`
- `THN_Sync_V2_CDC_Apply_Mutation_Plan.md`
- `THN_CLI_Sync_Apply_Backup_Safety.md`
- `THN_CLI_Recovery_Invariants_Ledger.md`

Nothing in this document may weaken or reinterpret those guarantees.

---

## Scope

This index covers **post-execution recovery only**.

It includes:
- Recovery concepts
- Recovery declarations
- Recovery control surfaces
- Recovery authority boundaries
- Recovery non-goals

It explicitly excludes:
- CDC rollback semantics
- Sync apply rollback behavior
- Backup restoration
- Diagnostics
- Observability
- Policy escalation
- Strict mode

Rollback is **not recovery**.  
Diagnostics are **not recovery**.  
Observability is **not recovery**.

---

## Definitions

**Rollback**  
A bounded, deterministic reversal of a failed or partial operation,
performed as part of the same execution context.

**Recovery**  
A deliberate, user-initiated, post-execution attempt to restore a system
to a known-safe or usable state after failure.

Recovery always occurs **after execution has completed** and **outside**
the original execution context.

---

## Recovery Surface Enumeration

### 1. Execution Engine

**Description**  
Core execution logic for sync, CDC apply, routing, or task execution.

**Status**: FORBIDDEN  
**Authority**: None  
**Persistence**: Forbidden  

**Notes**
- Engines must never attempt recovery
- Engines may fail or rollback only
- Recovery logic here is prohibited

---

### 2. CDC Rollback Paths

**Description**  
Rollback logic executed during CDC Stage 1 or Stage 2 apply.

**Status**: IMPLEMENTED (Rollback Only)  
**Authority**: Engine-scoped  
**Recovery**: Forbidden  

**Notes**
- Rollback is not recovery
- Rollback scope is execution-local
- Rollback must never attempt state reconstruction beyond declared paths

---

### 3. Backup Restoration

**Description**  
Restoration of files from backups created during apply or rollback.

**Status**: IMPLEMENTED (Rollback Support Only)  
**Authority**: Engine-scoped  
**Recovery**: Forbidden  

**Notes**
- Backup restore is deterministic
- Backup restore is not recovery
- No inference, guessing, or history inspection permitted

---

### 4. Diagnostics

**Description**  
Emission, aggregation, or presentation of diagnostic information.

**Status**: FORBIDDEN  
**Authority**: Observational only  
**Persistence**: Forbidden  

**Notes**
- Diagnostics may describe failures
- Diagnostics must never initiate recovery
- Diagnostics must never recommend actions implicitly

---

### 5. Observability Stores

#### TXLOG

**Status**: IMPLEMENTED  
**Authority**: Diagnostic only  
**Recovery**: Forbidden  

**Notes**
- TXLOG may record failure
- TXLOG must never be used to reconstruct or replay execution

---

#### Status DB

**Status**: IMPLEMENTED  
**Authority**: Authoritative (terminal success only)  
**Recovery**: Forbidden  

**Notes**
- Failed executions are intentionally absent
- Status DB must never drive recovery logic

---

### 6. CLI Commands

**Description**  
User-invoked CLI commands that could theoretically initiate recovery.

**Status**: DECLARED (NONE IMPLEMENTED)  
**Authority**: None  

**Notes**
- No recovery commands exist
- Any future recovery command must be:
  - Explicit
  - User-initiated
  - Versioned (ruleset named and immutable)
  - Dry-run capable
  - Fully auditable

---

### 7. Recovery Specifications

**Description**  
Declarative descriptions of recovery rules or procedures.

**Examples**
- Recovery model versions
- Recovery manifests
- Recovery specs

**Status**: DECLARED (INERT)  
**Authority**: Declarative only  
**Execution**: Forbidden  

**Notes**
- Specs do not imply execution
- Specs require explicit tooling to activate (future phase only)

---

### 8. GUI Surfaces

**Description**  
GUI presentation or orchestration of recovery-related workflows.

**Status**: DECLARED  
**Authority**: Presentation only  
**Execution**: Forbidden  

**Notes**
- GUI must never infer recovery state
- GUI may only present declared recovery options if explicitly enabled

---

### 9. Policy and Strict Mode

**Description**  
Diagnostic or policy systems that could influence recovery.

**Status**: FORBIDDEN  

**Notes**
- Recovery must never be policy-driven
- Recovery must never be implicit
- Recovery must never be triggered by diagnostics or strict mode

---

## Explicitly Forbidden Recovery Behaviors

The following **must not exist**:

- Automatic recovery
- Implicit recovery
- Diagnostic-triggered recovery
- Policy-triggered recovery
- Recovery based on missing data
- Recovery inference from TXLOG or Status DB
- Silent recovery attempts
- Recovery without explicit version declaration
- Recovery without user confirmation

Any occurrence is a defect.

---

## Appendix A — Recovery Surface Index (Table Only)

| Surface | Location | Status | Authority | Recovery Allowed |
|------|--------|--------|-----------|------------------|
| Execution engine | core engine | FORBIDDEN | None | No |
| CDC rollback | apply pipeline | IMPLEMENTED | Engine | No |
| Backup restore | backup logic | IMPLEMENTED | Engine | No |
| Diagnostics | diagnostics | FORBIDDEN | None | No |
| TXLOG | `.thn/txlog` | IMPLEMENTED | Diagnostic | No |
| Status DB | `.thn/status.db` | IMPLEMENTED | Authoritative | No |
| CLI recovery commands | CLI | DECLARED | None | Not yet |
| Recovery specs | docs / manifests | DECLARED | Declarative | Not yet |
| GUI recovery | GUI | DECLARED | Presentation | Not yet |

---

## Change Policy

Any modification to this document requires:

- Explicit acknowledgment
- Documentation update
- Alignment with recovery invariants
- Review of rollback and CDC semantics

Silent changes are prohibited.

---

## Summary

Recovery in THN is:

- Explicit
- Deliberate
- Versioned
- User-initiated
- Auditable
- Currently **non-existent**

This index ensures that recovery cannot emerge accidentally.

The absence of recovery behavior is intentional and enforced.

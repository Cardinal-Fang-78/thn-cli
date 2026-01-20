# THN CLI Unified History Introspection Surface Index

## Status

LOCKED — Reference Index Only  
Read-only. Declarative. No activation semantics.

---

This index was verified against a repository-wide audit of all history-adjacent
code paths and documentation as of commit `88fb074343f2f88251f8c613425851a7929fdeb0`.

The audit included exhaustive searches for:
- Replay, reconstruction, or rehydration logic
- History-driven branching or conditional behavior
- Implicit, automatic, or inferred mutation paths
- Recovery or repair coupling
- Persistence or authority escalation via history data

All discovered history references are:
- Read-only
- Diagnostic or presentation-only
- Explicitly prohibited from mutation, inference, recovery, or execution control

No undocumented or implicit Unified History surfaces exist at this commit.
Any future discovery of a history-driven execution, recovery, or mutation
path constitutes a defect.

---

## Purpose

This document enumerates **every surface where Unified History behavior
could theoretically appear within the THN CLI ecosystem**, and explicitly
classifies:

- What each surface is
- Where it lives
- Whether it is implemented, declared, or forbidden
- What authority it may have
- What it is explicitly prohibited from doing

This index exists to:

- Prevent accidental replay, recovery, or inference
- Make history-related surfaces auditable
- Eliminate ambiguity between history, diagnostics, rollback, and recovery
- Serve as the **single authoritative index** for Unified History design space

This document **does not define history behavior**.  
It defines **where history must not evolve beyond read-only observation**
and **where future surfaces may be declared inertly**.

Unified History evolution is governed by `THN_Unified_History_Evolution_and_Change_Policy.md`

---

## Relationship to Other Documents

This index is constrained by:

- `THN_CLI_Unified_History_Invariants_Ledger.md`
- `THN_CLI_DX2_Invariants.md`
- `DX-2.x Diagnostics Policy and Invariants`
- `THN_Recovery_Authority_and_Invariants.md`
- `THN_Recovery_Introspection_Surface_Index.md`
- `THN_CLI_Contract_Boundaries.md`

Nothing in this document may weaken or reinterpret those guarantees.

---

## Scope

This index covers **post-execution history only**.

It includes:
- History read models
- History aggregation surfaces
- History presentation paths
- History persistence boundaries
- History non-goals

It explicitly excludes:
- Execution engines
- CDC rollback
- Backup restoration
- Recovery
- Replay
- Diagnostics enforcement
- Policy escalation

History is **not recovery**.  
History is **not replay**.  
History is **not repair**.

---

## Definitions

**Unified History**  
A read-only aggregation of authoritative terminal execution records
(Status DB) and best-effort diagnostic lineage (TXLOG), presented without
inference, reconciliation, or mutation.

**Replay**  
Any attempt to re-execute, reconstruct, or simulate past execution.

Replay is **forbidden**.

---

## Unified History Surface Enumeration

### 1. Execution Engines

**Description**  
Core engines responsible for sync, CDC apply, routing, or task execution.

**Status**: FORBIDDEN  
**Authority**: None  
**History Access**: Forbidden  

**Notes**
- Engines must never read from history
- Engines must never branch behavior based on history
- History-driven execution is prohibited

---

### 2. Status DB

**Description**  
Authoritative persistence of terminal execution success only.

**Status**: IMPLEMENTED  
**Authority**: Authoritative (write-once, success-only)  
**History Role**: Source  

**Notes**
- Failed executions are intentionally absent
- Status DB must never be inferred against
- No reconstruction or reconciliation permitted

---

### 3. TXLOG

**Description**  
Best-effort diagnostic lineage log.

**Status**: IMPLEMENTED  
**Authority**: Diagnostic only  
**History Role**: Supplemental  

**Notes**
- TXLOG may be incomplete
- TXLOG must never be treated as authoritative
- No replay or synthesis permitted

---

### 4. Unified History Read Model

**Description**  
Composite read-only model combining Status DB and TXLOG.

**Status**: IMPLEMENTED  
**Authority**: Read-only aggregation  
**Mutation**: Forbidden  

**Notes**
- No inference across sources
- No backfilling or reconciliation
- Absence of data is preserved
- Pagination, limits, offsets, and truncation are presentation-only
  view constraints and are governed by
  `THN_CLI_Unified_History_Pagination_and_Selection_Semantics.md`

---

### 5. CLI Commands

**Description**  
User-invoked CLI commands exposing Unified History.

**Status**: IMPLEMENTED (Read-only)  
**Authority**: Presentation only  

**Notes**
- No command may mutate state
- No command may trigger recovery or replay
- JSON output is non-authoritative

---

### 6. Diagnostics

**Description**  
Diagnostic consumers or tooling that may reference history.

**Status**: FORBIDDEN  
**Authority**: None  

**Notes**
- Diagnostics may display history
- Diagnostics must never act on history
- History must not affect diagnostics severity or exit codes

---

### 7. Recovery Systems

**Description**  
Any recovery-related tooling or workflow.

**Status**: FORBIDDEN  

**Notes**
- History must never trigger recovery
- History must never be used to infer recovery scope
- Recovery (if ever introduced) is versioned and explicit

---

### 8. Replay or Reconstruction

**Description**  
Any attempt to re-run or reconstruct execution.

**Status**: FORBIDDEN  

**Notes**
- No replay commands exist
- No replay specs exist
- Any appearance is a defect

---

### 9. GUI Surfaces

**Description**  
GUI presentation of Unified History.

**Status**: DECLARED  
**Authority**: Presentation only  
**Execution**: Forbidden  

**Notes**
- GUI must never infer missing history
- GUI must never suggest actions implicitly

---

## Explicitly Forbidden History Behaviors

The following **must not exist**:

- Automatic replay
- Implicit recovery
- History-driven execution
- Inference from missing records
- Backfilling Status DB
- Synthesizing TXLOG entries
- Policy escalation based on history
- Diagnostic-triggered mutation

Any occurrence is a defect.

---

## Appendix A — Unified History Surface Index (Table Only)

| Surface | Location | Status | Authority | Mutation Allowed |
|------|--------|--------|-----------|------------------|
| Execution engines | core | FORBIDDEN | None | No |
| Status DB | `.thn/status.db` | IMPLEMENTED | Authoritative | No |
| TXLOG | `.thn/txlog` | IMPLEMENTED | Diagnostic | No |
| Unified history model | read layer | IMPLEMENTED | Read-only | No |
| CLI history commands | CLI | IMPLEMENTED | Presentation | No |
| Diagnostics | diagnostics | FORBIDDEN | None | No |
| Recovery systems | recovery | FORBIDDEN | None | No |
| Replay | any | FORBIDDEN | None | No |
| GUI history | GUI | DECLARED | Presentation | No |

---

## Change Policy

Any modification to this document requires:

- Explicit acknowledgment
- Update to the Unified History invariants ledger
- Cross-review against recovery and DX-2 invariants
- Documentation update

Silent changes are prohibited.

---

## Summary

Unified History in THN is:

- Read-only
- Non-inferential
- Non-replayable
- Non-recovering
- Non-operational

This index ensures history cannot evolve into execution,
recovery, or policy control accidentally.

The absence of replay or recovery is intentional and enforced.

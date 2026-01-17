# THN CLI DX-2 Introspection Surface Index

## Status

LOCKED — Reference Index Only  
Read-only. Declarative. No activation semantics.

---

## Verification Note

This index was verified against a repository-wide audit of diagnostic- and
policy-adjacent code and documentation as of commit `2d0b1339947d77f851d9635a66d1f64146a0ea39`.

No undocumented DX-2 surfaces, persistence paths, enforcement hooks, or
policy activation mechanisms were found.

Any future discovery of an unlisted surface is considered a defect and must
be addressed explicitly.

---

## Purpose

This document enumerates **every diagnostic- and policy-adjacent surface that exists or is declared under DX-2.x**, and explicitly classifies:

- What each surface does
- Where it lives
- Whether it is implemented or declared
- What authority it has
- What it is forbidden from doing

It exists to:

- Prevent accidental policy activation
- Make diagnostic surfaces auditable
- Eliminate ambiguity about responsibility and authority
- Serve as the **single index** for DX-2 introspection

This document **does not** define invariants.  
Those are defined in **DX-2.x Diagnostics Policy and Invariants**.

---

## Relationship to Other Documents

This index is constrained by:

- `DX-2.x Diagnostics Policy and Invariants`
- `diagnostics/diagnostics_consumer_contracts.md`
- `THN_CLI_Contract_Boundaries.md`
- `ERROR_CONTRACTS.md`

Nothing in this document may weaken or reinterpret those guarantees.

---

## Scope

This index covers:

- Diagnostic production
- Diagnostic aggregation
- Diagnostic normalization
- Strict-mode scaffolding
- Downgrade / escalation policy declarations
- Observability stores (TXLOG, Status DB)
- CLI and GUI read surfaces

It explicitly excludes:

- Engine execution semantics
- Sync apply behavior
- CDC mutation logic
- Backup safety
- Routing
- Exit code behavior

---

## DX-2 Surface Enumeration

### 1. Diagnostic Producers

**Description**  
Components that emit diagnostics describing observed state.

**Examples**
- Sync V2 inspectors (`thn sync inspect`)
- CDC payload completeness diagnostics
- Diagnostic emitters under `diagnostics/*_diag.py`
- CLI boundary registry diagnostics
- Developer tooling diagnostics (`thn dev cleanup temp`, etc.)

**Status**: IMPLEMENTED  
**Authority**: None  
**Persistence**: Forbidden  

**Notes**
- Producers may observe and describe only
- Producers must not normalize, interpret, or infer

---

### 2. Diagnostic Aggregators

**Description**  
Components that collect and assemble diagnostics without interpretation.

**Examples**
- `thn diag all`
- Hybrid-Standard diagnostic aggregation pipeline

**Status**: IMPLEMENTED  
**Authority**: None  
**Persistence**: Forbidden  

**Notes**
- Aggregation preserves producer intent
- No classification, escalation, or suppression

---

### 3. Diagnostic Normalization Boundary

**Description**  
The sole location where diagnostic output may be normalized for consumer stability.

**Location**
- Final CLI presentation boundary only

**Status**: IMPLEMENTED (BOUNDARY-LOCKED)  
**Authority**: None  
**Persistence**: Forbidden  

**Notes**
- Producers and engines must never normalize
- Normalization exists only to stabilize output shape
- Normalized data must never be written to disk

---

### 4. Strict Mode Scaffolding

**Description**  
Declared future enforcement surfaces that are currently inert.

**Examples**
- `--strict` flags on diagnostic read surfaces
- Strict evaluation helpers

**Status**: DECLARED (INERT)  
**Authority**: None  
**Enforcement**: None  

**Notes**
- Emits metadata only
- Does not alter exit codes or behavior
- Activation requires future explicit versioning

---

### 5. Downgrade / Escalation Policy Declarations

**Description**  
Documentation-only interpretation rules for diagnostic severity.

**Examples**
- Warning vs error classification models
- CI vs interactive interpretation guidance

**Status**: DECLARED (INERT)  
**Authority**: None  
**Runtime Effect**: Forbidden  

**Notes**
- No automatic activation
- No inference from environment, flags, or defaults
- Purely declarative

---

### 6. Observability Stores

#### TXLOG

**Description**  
Best-effort diagnostic observation of execution lineage.

**Status**: IMPLEMENTED  
**Authority**: Diagnostic only  
**Persistence**: Yes  

**Notes**
- May be incomplete
- Never inferred or repaired
- Never authoritative

---

#### Status DB

**Description**  
Authoritative record of terminal execution success.

**Status**: IMPLEMENTED  
**Authority**: Authoritative (terminal success only)  
**Persistence**: Yes  

**Notes**
- Failed executions are intentionally excluded
- No reconciliation with TXLOG

---

### 7. CLI Read Surfaces

**Description**  
Read-only interfaces for inspecting diagnostic and execution state.

**Examples**
- `thn sync history`
  - TXLOG-only mode
  - Unified history mode
  - Strict diagnostic overlay (read-only)
- `thn sync status`

**Status**: IMPLEMENTED  
**Mutation**: Forbidden  

**Notes**
- No inference
- No repair
- No policy enforcement

---

### 8. GUI Read Surfaces

**Description**  
Declared ingestion and presentation contracts for GUI consumers.

**Examples**
- Unified history ingestion
- Capability declaration surfaces
- Pagination and filtering contracts

**Status**: DECLARED  
**Authority**: Presentation only  
**Persistence**: Forbidden  

**Notes**
- GUI is a consumer, not an interpreter
- No semantic authority

---

### 9. Explicitly Forbidden Surfaces

The following **must not exist** in DX-2.x:

- Diagnostic-driven retries
- Diagnostic-driven aborts
- Exit-code modification from diagnostics
- Policy inference from missing data
- History repair or reconciliation
- CLI flags that silently activate policy
- Diagnostic influence on routing or CDC behavior

**Status**: FORBIDDEN

---

## Appendix A — DX-2 Surface Index (Table Only)

| Surface | Location | Status | Authority | Persistence |
|------|--------|--------|-----------|-------------|
| Diagnostic producers | `diagnostics/*` | IMPLEMENTED | None | No |
| Diagnostic aggregation | diag orchestration | IMPLEMENTED | None | No |
| Normalization boundary | CLI presentation | IMPLEMENTED | None | No |
| Strict mode scaffolding | CLI flags | DECLARED (INERT) | None | No |
| Downgrade policy | Documentation | DECLARED (INERT) | None | No |
| TXLOG | `.thn/txlog` | IMPLEMENTED | Diagnostic | Yes |
| Status DB | `.thn/status.db` | IMPLEMENTED | Authoritative | Yes |
| CLI history | `thn sync history` | IMPLEMENTED | Read-only | No |
| GUI history | GUI contracts | DECLARED | Presentation | No |

---

## Change Policy

Any modification to this document requires:

- Explicit acknowledgment
- Documentation update
- Alignment with DX-2 invariants
- Review of downstream consumers

Silent changes are prohibited.

---

## Summary

DX-2 introspection is **enumerated, bounded, and inert by design**.

This index ensures that:
- All surfaces are visible
- All authority is explicit
- No future enforcement can occur accidentally

The absence of behavior is intentional.

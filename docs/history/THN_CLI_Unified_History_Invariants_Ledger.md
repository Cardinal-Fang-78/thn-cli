# THN CLI Unified History Invariants Ledger

## Status

LOCKED — Declarative Reference Only  
Read-only. Non-inferential. No activation semantics.

---

## Verification Note

This ledger was verified against a repository-wide audit of Unified History,
TXLOG, Status DB, and history-related CLI/doc surfaces as of commit `88fb074343f2f88251f8c613425851a7929fdeb0`.

No undocumented Unified History surfaces, persistence paths, inference hooks,
or reconciliation mechanisms were found.

Any future discovery of an unlisted surface or behavior is considered a defect
and must be addressed explicitly.

---

## Purpose

This document is the **concrete, implementation-adjacent ledger** of the
Unified History system’s non-negotiable invariants.

It exists to:

- Prevent semantic drift in read surfaces
- Prevent inference or synthesis from partial observability
- Freeze authority boundaries between Status DB, TXLOG, and presentation
- Establish explicit change policy for history semantics

This ledger does not introduce behavior.  
It describes what is already locked or intentionally absent.

---

## Scope

This ledger governs **Unified History read semantics only**, including:

- Unified history aggregation rules (read-only)
- Authority boundaries between data sources
- Presentation and consumer guarantees
- Strict overlays when present (read-only, inert)

It does **not** govern:

- Engine execution semantics
- Sync apply or CDC mutation plans
- Rollback behavior (execution-scoped)
- Recovery behavior (post-execution; currently non-operational)
- Diagnostics policy escalation or enforcement

---

## Definitions

**Status DB**  
The sole authoritative record of terminal execution success as defined by the engine.

**TXLOG**  
A diagnostic, best-effort lineage record. It may be incomplete and must never be treated as authoritative.

**Unified History**  
A read-only composite view that presents both authoritative and diagnostic signals **without**
reconciling, repairing, inferring, or synthesizing missing information.

Unified History evolution is governed by `THN_Unified_History_Evolution_and_Change_Policy.md`

**Non-inferential**  
No component may guess execution outcomes, repair gaps, or derive truth from absence.

---

## Core Invariants (Non-Negotiable)

### 1. Unified History Is Read-Only

Unified history may:
- Read
- Aggregate
- Present
- Annotate provenance

Unified history must never:
- Mutate execution state
- Write to disk
- Write to TXLOG
- Write to Status DB
- Create scaffolds or folders
- Trigger retries or follow-up actions

---

### 2. Status DB Is the Sole Authoritative Execution Record

- Status DB terminal success records are authoritative.
- Absence of a Status DB record is **not** evidence of failure.
- Status DB must never be “completed” using TXLOG.
- Unified history must never invent terminal outcomes not present in Status DB.

---

### 3. TXLOG Is Diagnostic-Only and May Be Incomplete

- TXLOG is best-effort diagnostic lineage only.
- TXLOG may be missing records and this is acceptable.
- Missing TXLOG must never be treated as an error by unified history.
- Unified history must never infer outcomes from TXLOG presence/absence.

---

### 4. No Reconciliation Between Status DB and TXLOG

Unified history must not:
- Reconcile
- Repair
- Merge-as-truth
- Prefer one store to “fix” the other
- Derive “final” outcomes by combining signals

Unified history may:
- Present both signals side-by-side
- Clearly label provenance per field or record
- Leave gaps explicit

Absence is data. It is not permission to infer.

---

### 5. Absence Is Never Interpreted

The following are explicitly forbidden:

- “No record implies failure”
- “Missing TXLOG implies nothing happened”
- “Missing Status DB implies rollback”
- “TXLOG present implies success”

All such interpretations are forbidden unless explicitly recorded as authoritative fact
by the engine (Status DB) or explicitly emitted as diagnostic observation (TXLOG).

---

### 6. Provenance Must Be Explicit

Any unified history payload must make provenance unambiguous:

- What is sourced from Status DB
- What is sourced from TXLOG
- What is computed as presentation-only metadata (if any)

Computed metadata must be:
- Clearly labeled
- Non-authoritative
- Non-semantic
- Optional for consumers

---

### 7. Ordering Must Be Explicit and Non-Semantic

If unified history presents ordering:

- Ordering must be explicitly documented (e.g., by timestamp, by source ordering).
- Ordering must never imply “truth,” “priority,” or “finality.”
- Ordering must never be used to infer missing outcomes.

If ordering is not well-defined, unified history must declare that explicitly.

Pagination, limits, offsets, and truncation are governed by
`THN_CLI_Unified_History_Pagination_and_Selection_Semantics.md` and are
presentation-only.

---

### 8. Strict Mode Overlays Are Read-Only and Inert

If a strict overlay exists on unified history read surfaces:

- It must not modify engine behavior
- It must not modify exit codes
- It must not block execution
- It must not trigger recovery
- It may only add labels, warnings, or metadata to the output

Strict overlay activation must be:
- Explicit
- Declared
- Versioned if semantics ever change

By default, strict overlays are inert.

---

### 9. Consumers Must Not Treat Unified History as Engine Truth

Unified history outputs are:

- Presentation-safe
- Read-only
- Non-inferential

Consumers must not:
- Use unified history as the source of execution authority
- Treat the absence of records as enforceable policy
- Automatically trigger mutation, recovery, or enforcement actions

Authoritative decisions must use authoritative sources explicitly (Status DB) and only
within declared contracts.

---

### 10. No Recovery or Replay Is Permitted

Unified history must never:

- Attempt recovery
- Attempt replay
- Suggest operational repair
- Construct “replay plans”
- Provide “fix-up” actions derived from missing data

If future replay or recovery is implemented, it must be:
- Explicitly introduced
- Separately versioned
- Policy-gated
- Auditable
- Outside unified history read semantics

---

## Authority Boundary Summary

| Layer | Authority | Notes |
|------|-----------|------|
| Engine | Absolute | Produces authoritative behavior and terminal success records |
| Status DB | Authoritative | Terminal success only; absence is not failure |
| TXLOG | Diagnostic | Best-effort lineage only; may be incomplete |
| Unified history | Presentation | Read-only composite; no inference, no repair |
| CLI | Presentation | Renders declared contracts; must not reinterpret |
| GUI | Consumer | Presentation only; must not infer or enforce |

---

## Explicit Non-Goals

Unified history explicitly does **not**:

- Enforce policy
- Determine success/failure when records are absent
- Repair or reconcile observability gaps
- Provide recovery or replay tooling
- Normalize, reinterpret, or “fix” history
- Guarantee completeness of diagnostic lineage

Absence of these behaviors is intentional.

---

## Appendix A — Unified History Surface Index (Table Only)

| Surface | Location | Status | Authority | Persistence |
|------|--------|--------|-----------|-------------|
| Status DB | `.thn/status.db` | IMPLEMENTED | Authoritative | Yes |
| TXLOG | `.thn/txlog` | IMPLEMENTED | Diagnostic | Yes |
| Unified history reader | `thn sync history` (unified) | IMPLEMENTED | Presentation | No |
| TXLOG-only history view | `thn sync history` (txlog) | IMPLEMENTED | Presentation | No |
| Strict overlay (history) | `thn sync history --strict` (if present) | DECLARED / INERT | None | No |
| GUI ingestion contracts | GUI history docs | DECLARED | Presentation | No |

---

## Change Policy

Any change to these invariants requires:

- Explicit versioning or documented rationale (as appropriate)
- Changelog entry (intent and outcome)
- Documentation update (this ledger and any related contracts)
- Review acknowledgment

Silent changes are prohibited.

---

## Summary

Unified history is a **read-only, non-inferential composite view**.

It exists to make history visible without:
- Repair
- Reconciliation
- Inference
- Policy activation
- Recovery behavior

The absence of these behaviors is the guarantee.

End of document.

# THN CLI Unified History Field Contracts v1

LOCKED — Design-Only Field Contract  
Read-only. Declarative. No runtime effect.

This document defines **field-level contracts** for the Unified History
Schema v1. It specifies **presence, meaning, authority, and prohibitions**
for each field without introducing validation, enforcement, migration,
or execution semantics.

Verified against repository state at commit:
`99e3d316b545329bd468afe2971beea4022f510e`

---

## Purpose

This document exists to:

- Define **field-level meaning and guarantees** for Unified History
- Prevent semantic drift without structural change
- Explicitly prohibit inferred or operational interpretations
- Establish a stable reference for documentation and consumers

This document governs **interpretation**, not behavior.

---

## Scope

This document applies to:

- Unified History payloads emitted by:
  - `thn sync history --json`
  - GUI unified history ingestion APIs
- Schema Version: **Unified History v1**

This document does **not** apply to:

- Execution engines
- Diagnostics engines
- Recovery systems
- Migration tooling
- Validation or enforcement layers

---

## Normative References

This document is subordinate to:

- `THN_CLI_Unified_History_Invariants_Ledger.md`
- `THN_CLI_Unified_History_Introspection_Surface_Index.md`
- `THN_Unified_History_Evolution_and_Change_Policy.md`
- `THN_CLI_Unified_History_Schema_v1.md`

In case of conflict, **invariants take precedence**.

---

## Top-Level Unified History Object

### Field: `history`

| Property | Contract |
|--------|---------|
| Presence | REQUIRED |
| Type | Object |
| Authority | Read-only aggregation |
| Mutation | Forbidden |
| Inference | Forbidden |

**Meaning**

The `history` object represents a **composite, read-only view** of
execution observability sources.

It does **not** represent:
- System state
- Execution capability
- Recovery readiness
- Completeness guarantees

**Prohibitions**

The presence or absence of `history` MUST NOT be used to:
- Infer execution success
- Trigger recovery or replay
- Modify behavior
- Escalate diagnostics
- Construct plans

---

## Status DB Contribution

### Field: `status`

| Property | Contract |
|--------|---------|
| Presence | OPTIONAL |
| Type | Object |
| Authority | Authoritative (terminal success only) |
| Completeness | Partial by design |
| Mutation | Forbidden |

**Meaning**

Represents **terminal successful execution records only**.

Absence of `status`:
- Does NOT imply failure
- Does NOT imply rollback
- Does NOT imply incomplete execution

**Prohibitions**

Consumers MUST NOT:
- Infer failure from absence
- Reconstruct execution
- Backfill missing entries
- Treat this field as a control signal

---

## TXLOG Contribution

### Field: `txlog`

| Property | Contract |
|--------|---------|
| Presence | OPTIONAL |
| Type | Object |
| Authority | Diagnostic only |
| Completeness | Best-effort |
| Mutation | Forbidden |

**Meaning**

Represents diagnostic lineage and observation emitted during execution.

TXLOG is **non-authoritative** and may be incomplete.

**Prohibitions**

Consumers MUST NOT:
- Treat TXLOG as authoritative
- Reconcile TXLOG with Status DB
- Infer intent or execution outcome
- Repair or synthesize entries

---

## Unified Entry List

### Field: `entries`

| Property | Contract |
|--------|---------|
| Presence | REQUIRED (may be empty) |
| Type | Array |
| Ordering | Presentation-only |
| Authority | None |

**Meaning**

A presentation-safe aggregation of history entries derived from
Status DB and TXLOG.

Ordering:
- Is not guaranteed to represent causality
- Is not guaranteed to be complete

**Prohibitions**

Consumers MUST NOT:
- Infer execution order
- Infer dependency chains
- Replay entries
- Treat ordering as authoritative

---

## Strict Diagnostics Overlay (Optional)

### Field: `strict`

| Property | Contract |
|--------|---------|
| Presence | OPTIONAL |
| Type | Object |
| Authority | Diagnostic-only |
| Activation | Inert by default |

**Meaning**

Represents **diagnostic interpretation overlays** applied to the unified
history payload.

Strict overlays:
- Do not alter history
- Do not alter execution
- Do not alter exit codes

**Prohibitions**

Strict overlays MUST NOT:
- Trigger mutation
- Trigger recovery
- Affect routing
- Escalate authority

---

## Cross-Field Guarantees

Unified History fields collectively guarantee:

- No inference across sources
- No reconciliation
- No synthesis
- No mutation
- No execution coupling

Absence of data is preserved and meaningful.

---

## Explicitly Forbidden Interpretations

The following interpretations are **forbidden**:

- “Missing status implies rollback”
- “TXLOG implies failure”
- “History implies recoverability”
- “History completeness”
- “History-driven decision making”

Any such interpretation constitutes a defect.

---

## Change Policy

Any change to field meaning requires:

1. Explicit documentation update
2. Cross-review against invariants and schema
3. Classification under the Evolution Policy

Silent or implicit changes are prohibited.

---

## Summary

Unified History field contracts ensure:

- Stable interpretation
- Non-escalation
- Safety against replay or recovery
- Future evolution without ambiguity

This document locks **what fields mean**, not what the system does.

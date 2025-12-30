# THN Sync V2
## Status DB Read Surface Contract

---

## Purpose

Defines the **authorized read surface** for the Sync V2 Status DB.

This contract specifies **what may be read**, **how it may be read**, and
**what guarantees are provided** — without asserting any execution,
coordination, or reconciliation behavior.

This document exists to prevent:
- Ad-hoc read helpers
- Inferred execution state
- Implicit coupling to TXLOG or filesystem state
- Backward-incompatible CLI growth

---

## Authority Model

The Status DB is **authoritative history**, but **read-only**.

Roles:
- Engine executes
- TXLOG observes
- Status DB records outcomes
- Read surface **reports recorded facts only**

The read surface:
- Never infers
- Never reconstructs
- Never correlates across subsystems
- Never predicts future state

---

## Read Scope

The read surface may expose **only persisted rows** from the Status DB.

Permitted facts:
- Recorded execution timestamp
- Target name
- Operation type
- Mode (raw-zip, cdc-delta, rollback)
- Dry-run flag
- Success flag
- Manifest hash (if recorded)
- Envelope path (if recorded)
- Source root (if recorded)
- File count (if recorded)
- Total size (if recorded)
- Backup ZIP path (if recorded)
- Destination path
- Notes blob (opaque)

No additional data may be synthesized.

---

## Prohibited Behavior

The read surface MUST NOT:

- Inspect filesystem state
- Read TXLOG files
- Inspect snapshots
- Inspect registry data
- Infer missing timestamps
- Infer ordering beyond recorded IDs
- Merge multiple history sources
- Invent transaction identity
- Apply policy or filtering logic beyond explicit parameters

---

## Read Operations (Conceptual)

The following **conceptual operations** are permitted:

- **List**
  - Return the most recent N entries
- **Filter**
  - By target
  - By operation
- **Fetch**
  - By primary identifier

All filters are **exact-match** and **non-semantic**.

---

## Ordering Guarantees

Ordering is defined strictly by **insertion order**.

- No guarantees of wall-clock correctness
- No guarantees of monotonic timestamps
- No guarantees across multiple writers
- No inferred causality

---

## Error Semantics

Read operations must:

- Return empty results when no data exists
- Never throw due to missing data
- Never block execution paths
- Never degrade engine or TXLOG behavior

Failures to read the Status DB are diagnostic-only.

---

## Relationship to TXLOG

Status DB reads are **completely independent** of TXLOG.

- No reconciliation
- No comparison
- No merging
- No fallback behavior

TXLOG may exist without Status DB.
Status DB may exist without TXLOG.

---

## Relationship to CLI

The CLI may expose Status DB reads **only through this contract**.

The CLI must:
- Preserve field names verbatim
- Avoid re-labeling semantics
- Avoid summarization beyond display formatting
- Avoid introducing derived fields

---

## Forward Compatibility

This contract allows:
- Additional optional fields
- New operations recorded by the engine
- New CLI display modes

This contract forbids:
- Removal of existing fields
- Semantic reinterpretation
- Implicit joins with other subsystems

---

## Contract Status

LOCKED — READ-ONLY AUTHORITATIVE HISTORY

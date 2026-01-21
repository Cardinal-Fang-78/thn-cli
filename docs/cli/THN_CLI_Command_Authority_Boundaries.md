# THN CLI Command Authority Boundaries

## Status

LOCKED — Declarative Authority Contract  
Read-only. No runtime effect. No activation semantics.

---

## Purpose

This document defines the **authoritative boundaries of all THN CLI commands**.

It exists to:

- Prevent accidental escalation of CLI authority
- Explicitly classify which commands may mutate state
- Lock read-only and diagnostic-only commands as non-authoritative
- Prevent history-, diagnostic-, or strict-mode–driven execution
- Provide a stable reference for future command additions

This document does **not** define command behavior.  
It declares **what commands are allowed to do** and, critically, **what they must never do**.

---

## Authority Model

All THN CLI commands fall into **exactly one** of the following authority classes.

### 1. Execution Authority

Commands that:
- Mutate filesystem or project state
- Apply migrations, syncs, or recovery actions
- Execute engine-controlled behavior

Execution authority is **explicit**, **opt-in**, and **command-scoped**.

Execution-authoritative commands must never:
- Read Unified History to make decisions
- Read diagnostics to infer correctness
- Escalate policy based on historical absence or presence

---

### 2. Presentation Authority (Read-Only)

Commands that:
- Read existing data
- Aggregate or format results
- Emit JSON or human-readable output only

Presentation authority is:
- Read-only
- Non-inferential
- Non-operational

Presentation commands must never:
- Mutate state
- Trigger execution
- Activate recovery
- Enforce policy

---

### 3. Diagnostic Authority (Observational Only)

Commands that:
- Inspect state
- Emit warnings or annotations
- Classify or normalize diagnostic output

Diagnostic authority is:
- Non-blocking
- Non-enforcing
- Explicitly non-authoritative

Diagnostics may **describe**, but must never **decide**.

---

## Command Classification

### A. Execution-Authoritative Commands

These commands are the **only CLI surfaces permitted to mutate state**.

| Command | Authority | Notes |
|------|---------|------|
| `thn sync apply` | Execution | Engine-owned mutation |
| `thn sync delta apply` | Execution | CDC mutation |
| `thn migrate apply` | Execution | Versioned migration |
| `thn make` | Execution | Scaffold creation |
| `thn accept` | Execution | Policy-gated mutation |
| `thn routing apply` | Execution | Routing mutation |
| `thn registry *` (mutating) | Execution | Registry writes |
| `thn recovery apply` | Execution | Explicit, policy-gated |

**Invariants**
- Execution commands must never consult Unified History
- Diagnostics must not alter execution outcome
- Strict mode must not escalate authority

---

### B. Read-Only History Presentation Commands

These commands expose **history or lineage data only**.

| Command | Authority | Notes |
|------|---------|------|
| `thn sync history` | Presentation | JSON-only |
| `thn drift history` | Presentation | Diagnostic timeline |
| `thn snapshots diff` | Presentation | Structural comparison |
| `thn snapshots inspect` | Presentation | Read-only |
| `thn sync status` | Presentation | Alias, JSON-enforced |
| GUI history API | Presentation | Read-only contract |

**Invariants**
- No inference
- No repair
- No reconciliation
- No execution authority

---

### C. Diagnostic-Only Commands

These commands are **observational probes only**.

| Command | Authority | Notes |
|------|---------|------|
| `thn inspect *` | Diagnostic | Read-only |
| `thn diag *` | Diagnostic | Normalized output |
| `thn drift preview` | Diagnostic | No enforcement |
| `thn drift explain` | Diagnostic | No mutation |
| `thn recover inspect` | Diagnostic | Non-blocking |
| Snapshot lineage tools | Diagnostic | Annotative only |

**Invariants**
- Diagnostics must never block execution
- Diagnostics must never trigger recovery
- Diagnostics must never escalate policy

---

## Strict Mode Semantics

Strict mode within the THN CLI is:

- Explicitly opt-in
- Diagnostic-only
- Non-blocking
- Non-enforcing

Strict mode may:
- Add warnings
- Add metadata
- Increase diagnostic verbosity

Strict mode must never:
- Change exit codes
- Block execution
- Trigger recovery
- Enforce policy
- Escalate authority

---

## Explicitly Forbidden Authority

The following **must not exist**:

- History-driven execution
- Diagnostic-driven recovery
- Replay or reconstruction commands
- Implicit repair or reconciliation
- Policy escalation based on absence of records
- Strict-mode enforcement

Any appearance of the above constitutes a defect.

---

## Relationship to Other Governance Documents

This document is constrained by:

- `THN_CLI_Command_Boundaries.md`
- `THN_CLI_Unified_History_Invariants_Ledger.md`
- `THN_CLI_Unified_History_Introspection_Surface_Index.md`
- `THN_Recovery_Authority_and_Invariants.md`
- `THN_CLI_DX2_Invariants.md`
- `THN_CLI_Diagnostics_Policy_Escalation.md`

Nothing in this document may weaken or reinterpret those guarantees.

---

## Change Policy

Any change to command authority requires:

1. Explicit documentation update
2. Changelog entry (intent and outcome)
3. Review of Unified History, Diagnostics, and Recovery invariants

Silent changes are prohibited.

---

## Summary

THN CLI command authority is:

- Explicit
- Bounded
- Non-inferential
- Non-escalating

Commands either **act**, **present**, or **observe**.

No command may silently cross that boundary.

End of document.

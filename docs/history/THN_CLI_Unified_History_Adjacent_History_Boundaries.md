# THN CLI Unified History — Adjacent History Boundaries

LOCKED — Design-Only Boundary Declaration  
Read-only. Declarative. No runtime effect.

This document defines **explicit boundaries between Unified History and
other history-like systems** within the THN CLI ecosystem. It exists to
prevent semantic bleed, inference, or conflation between distinct forms
of historical data.

Verified against repository state at commit:
`d2a4eabf570e083029a94147932158fa67407fab`

---

## Purpose

This document exists to:

- Explicitly define **what Unified History is not**
- Prevent accidental convergence of unrelated history systems
- Eliminate ambiguity caused by the overloaded term “history”
- Lock non-interoperability between distinct historical domains
- Provide future contributors with a clear mental model

This document governs **interpretation and boundaries only**, not
implementation or behavior.

---

## Core Principle

> **Not all history is Unified History.**

The presence of multiple history-like systems in THN is intentional.
They serve different purposes, carry different authority, and must
never be merged, inferred across, or treated as substitutes.

---

## Definition — Unified History

**Unified History** is:

- A **read-only, non-inferential composite view**
- Combining:
  - Authoritative terminal execution records (Status DB)
  - Best-effort diagnostic lineage (TXLOG)
- Presented without:
  - Reconciliation
  - Repair
  - Inference
  - Replay
  - Recovery
  - Execution control

Unified History exists solely to **observe past execution outcomes and
diagnostic traces without interpretation**.

---

## Adjacent History Systems (Non-Unified)

The following systems are **explicitly not Unified History**, even though
they may contain historical or timeline-oriented data.

### 1. Drift History

**Description**  
Records accepted drift, migrations, or scaffold evolution over time.

**Purpose**
- Track intentional structural changes
- Support auditability of accepted differences
- Provide migration lineage

**Key Properties**
- Deterministic
- Persisted
- Scoped to scaffold evolution

**Boundary Rule**
- Drift history must never be merged into Unified History
- Unified History must never infer execution outcomes from drift history

---

### 2. Migration History

**Description**  
Records migration operations and manifest-level transitions.

**Purpose**
- Track schema or structure evolution
- Support migration audit trails

**Key Properties**
- Explicitly authored
- Version-scoped
- Mutation-adjacent (but not execution)

**Boundary Rule**
- Migration history is not execution history
- Unified History must not infer execution success from migration presence

---

### 3. Snapshot Diff History

**Description**  
Represents differences between snapshots over time.

**Purpose**
- Visualize or compute structural changes
- Support diagnostics or comparison

**Key Properties**
- Derived
- Comparative
- Non-authoritative

**Boundary Rule**
- Snapshot diffs must never be treated as execution records
- Unified History must not incorporate snapshot diff timelines

---

### 4. Registry Event History

**Description**  
Records registry-level events (creation, updates, metadata changes).

**Purpose**
- Track configuration or registry state changes
- Support administrative auditability

**Key Properties**
- Administrative
- Metadata-focused
- Non-execution

**Boundary Rule**
- Registry history must never be interpreted as execution history
- Unified History must not aggregate registry events

---

### 5. Diagnostics History

**Description**  
Represents diagnostic observations, warnings, or reports over time.

**Purpose**
- Aid troubleshooting
- Provide visibility into diagnostic signals

**Key Properties**
- Best-effort
- Non-authoritative
- Presentation-oriented

**Boundary Rule**
- Diagnostics history must not drive Unified History semantics
- Unified History must not be used to escalate diagnostics

---

## Explicitly Forbidden Conflations

The following are **explicitly prohibited**:

- Treating drift history as execution success
- Treating migration history as proof of apply
- Treating snapshot diffs as execution outcomes
- Treating registry events as execution timelines
- Treating diagnostic timelines as authoritative history
- Merging multiple history systems into a single inferred narrative

Any such behavior constitutes a defect.

---

## Authority Summary

| History System        | Authority Level      | Execution-Coupled |
|----------------------|---------------------|-------------------|
| Unified History      | Presentation-only    | No                |
| Status DB            | Authoritative        | Yes (success-only)|
| TXLOG                | Diagnostic           | No                |
| Drift History        | Structural audit     | No                |
| Migration History    | Structural audit     | No                |
| Snapshot Diffs       | Comparative          | No                |
| Registry History     | Administrative       | No                |
| Diagnostics History  | Diagnostic           | No                |

---

## Governance

This document is subordinate to:

- `THN_CLI_Unified_History_Invariants_Ledger.md`
- `THN_CLI_Unified_History_Introspection_Surface_Index.md`
- `THN_Unified_History_Evolution_and_Change_Policy.md`
- `THN_CLI_Contract_Boundaries.md`

In case of conflict:
**Invariants → Introspection Surface Index → Adjacent Boundaries**

---

## Change Policy

Any change to the boundaries defined here requires:

1. Explicit documentation update
2. Cross-review against invariants and surface index
3. Change classification under the evolution policy

Silent convergence of history systems is prohibited.

---

## Summary

Unified History is **one history system among many**.

It is:
- Read-only
- Non-inferential
- Non-authoritative
- Non-operational

Other history systems exist for valid reasons, but they must remain
**semantically isolated**.

This document ensures that “history” in THN never becomes ambiguous,
overloaded, or implicitly authoritative.

End of document.

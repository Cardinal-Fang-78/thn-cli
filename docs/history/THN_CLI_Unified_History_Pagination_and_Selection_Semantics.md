# THN CLI Unified History Pagination and Selection Semantics

LOCKED — Design-Only Semantics Declaration  
Read-only. Declarative. No runtime effect.

This document defines **pagination, selection, truncation, and bounded-view
interpretation semantics** for Unified History read surfaces. It does **not**
introduce behavior, enforcement, validation, inference, replay, recovery, or
execution control.

Verified against repository state at commit:
`3c42122e269eacd00639b0f394bbea308a35ef87`

---

## Purpose

This document exists to:

- Define how **bounded Unified History views** must be interpreted
- Eliminate ambiguity around pagination, limits, offsets, and selection
- Prevent inference from partial or truncated history views
- Lock pagination as a **presentation-only concern**
- Ensure consistent interpretation across CLI and GUI consumers

This document governs **interpretation only**, not execution.

---

## Core Principle

> **Pagination describes visibility, not completeness.**

A paginated or truncated Unified History view:
- Is never complete by implication
- Does not represent the full execution record
- Must not be treated as authoritative history
- Must not imply success, failure, recency, or priority

Pagination is **presentation metadata**, not semantic signal.

---

## Definitions

**Pagination**  
Any mechanism that limits the number of Unified History records returned
(e.g., `limit`, `offset`, page size).

**Selection**  
Any filtering or slicing of Unified History records based on parameters,
constraints, or presentation needs.

**Bounded View**  
A Unified History payload that intentionally exposes only a subset of
available records.

**Unbounded View**  
A Unified History payload that attempts to expose all available records
without truncation (subject to storage limits).

---

## Global Interpretation Rules

The following rules apply to **all Unified History pagination and selection**:

1. Pagination MUST NOT imply completeness
2. Pagination MUST NOT imply ordering semantics beyond presentation
3. Pagination MUST NOT imply recency guarantees
4. Pagination MUST NOT be used to infer missing executions
5. Pagination MUST NOT influence behavior, recovery, or diagnostics

Consumers must assume **any bounded view is incomplete**.

---

## Selection Semantics

When Unified History records are selected or filtered:

- Selection criteria are **presentation-only**
- Selection does not alter underlying history
- Selection does not establish priority or importance
- Selection must never be interpreted as policy

Selected records are **visible records**, not **relevant records**.

---

## Pagination Parameters (Interpretation Only)

If pagination parameters exist (e.g., limit, offset, page):

- They describe **how much is shown**
- They do not describe **what exists**
- They do not guarantee stable inclusion across calls
- They do not guarantee deterministic completeness

Pagination parameters are **view constraints**, not history constraints.

---

## Ordering Interaction

Pagination may interact with ordering, but:

- Ordering remains non-semantic
- Ordering must not be interpreted as causality
- Ordering must not be interpreted as execution correctness
- Pagination must not be used to “find” success or failure

If ordering is applied, it must already comply with
`THN_CLI_Unified_History_Temporal_Semantics.md`.

---

## CLI Interpretation Rules

CLI consumers MUST:

- Clearly indicate when output is bounded or limited
- Avoid language implying completeness (e.g., “all”, “full history”)
- Avoid suggesting remediation based on missing records
- Avoid interpreting pagination as success/failure indicators

CLI output remains **descriptive only**.

---

## GUI Interpretation Rules

GUI consumers MUST:

- Treat paginated views as partial by default
- Avoid inferred timelines across pages
- Avoid visual cues implying “end state” or “finality”
- Avoid action affordances derived from partial views

GUI pagination is **navigation**, not analysis.

---

## Prohibited Behaviors

The following are explicitly forbidden:

- Treating a page boundary as a semantic boundary
- Inferring “most recent success” from page contents
- Inferring failure from absence beyond page limits
- Triggering recovery, replay, or escalation due to truncation
- Synthesizing “missing” history entries

Any such behavior is a defect.

---

## Governance

This document is subordinate to:

- `THN_CLI_Unified_History_Invariants_Ledger.md`
- `THN_CLI_Unified_History_Field_Contracts_v1.md`
- `THN_CLI_Unified_History_Temporal_Semantics.md`
- `THN_Unified_History_Evolution_and_Change_Policy.md`

In case of conflict:
**Invariants → Field Contracts → Temporal Semantics → Pagination Semantics**

---

## Change Policy

Any change to pagination or selection interpretation requires:

1. Explicit documentation update
2. Cross-review against temporal and nullability semantics
3. Classification under the Unified History evolution policy

Silent reinterpretation is prohibited.

---

## Summary

Unified History pagination semantics are:

- Explicit
- Non-inferential
- Presentation-only
- Non-authoritative
- Non-actionable

Pagination limits visibility — **never meaning**.

This document ensures Unified History consumers cannot accidentally
convert partial views into inference, policy, or control.

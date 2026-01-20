# THN CLI Unified History Integrity and Non-Guarantees

LOCKED — Design-Only Integrity Declaration  
Read-only. Declarative. No runtime effect.

This document explicitly declares **what Unified History does not and cannot
guarantee**, even under ideal conditions. It exists to prevent implicit,
assumed, or inferred guarantees from emerging through documentation,
presentation, or consumer behavior.

Verified against repository state at commit:
`2ba4e1a43e06caeb8b7ceb79f3a05ae5cd967c8a`

---

## Purpose

This document exists to:

- Eliminate implicit assumptions about Unified History correctness or completeness
- Prevent consumers from relying on properties that are intentionally absent
- Lock expectations around partial, best-effort observability
- Close interpretive gaps left by “well-behaved” or “ideal” execution scenarios
- Provide a definitive reference for **what is not promised**

This document governs **expectations**, not behavior.

---

## Core Principle

> **Unified History is informative, not comprehensive.**

The absence of a guarantee is intentional.

No consumer may treat Unified History as complete, authoritative, or
self-sufficient.

See also: `THN_CLI_Unified_History_Adjacent_History_Boundaries.md`

---

## Explicit Non-Guarantees

Unified History explicitly does **not** guarantee the following.

### 1. Completeness

Unified History does **not** guarantee that all executions are visible.

Reasons include (but are not limited to):
- Diagnostic loss
- Partial persistence
- Best-effort logging
- Bounded views
- Consumer-requested limits
- Source-specific retention policies

Absence of data is expected and valid.

---

### 2. Symmetry Between Sources

Unified History does **not** guarantee symmetry between Status DB and TXLOG.

Valid states include:
- Status DB present without TXLOG
- TXLOG present without Status DB
- Both present
- Both absent

No reconciliation is permitted.

---

### 3. Ordering Across Sources

Unified History does **not** guarantee a single, canonical execution order
across sources.

Any ordering that exists:
- Is source-local
- Is presentation-only
- Must not be treated as causality or truth

---

### 4. Temporal Accuracy

Unified History does **not** guarantee:
- Clock synchronization
- Timestamp monotonicity
- Cross-source temporal alignment
- Precision or resolution consistency

Timestamps describe observation, not execution truth.

---

### 5. Recency Semantics

Unified History does **not** guarantee that:
- The “latest” entry is meaningful
- The most recent record implies success
- Older entries are superseded
- A visible record represents the current state

Recency is a **view**, not a guarantee.

---

### 6. Durability or Retention

Unified History does **not** guarantee:
- Infinite retention
- Persistence across upgrades
- Identical retention policies per source
- Stable storage lifetimes

Consumers must tolerate disappearance.

---

### 7. Identity Stability

Unified History does **not** guarantee:
- Stable identifiers across restarts
- Stable identifiers across sources
- Referential integrity beyond a single payload

Identity is contextual, not global.

---

### 8. Exhaustiveness of Surfaces

Unified History does **not** guarantee that:
- All possible history views are exposed
- All internal observability paths are surfaced
- All future surfaces are backward-compatible

Only declared surfaces are governed.

---

### 9. Replayability

Unified History does **not** guarantee:
- Replay feasibility
- Reconstructable execution state
- Deterministic re-execution
- Audit-grade completeness

Replay is explicitly out of scope.

---

### 10. Safety for Control Decisions

Unified History does **not** guarantee safety for:
- Automation
- Enforcement
- Policy decisions
- Recovery triggers
- Rollback initiation

Using Unified History for control flow is forbidden.

---

## What Integrity Means (Clarified)

Integrity in Unified History means:

- Honest presentation of available data
- Explicit provenance labeling
- Preservation of absence
- No synthesis or repair
- No semantic escalation

Integrity does **not** mean correctness, completeness, or authority.

---

## Consumer Obligations

Consumers of Unified History must:

- Treat all views as partial by default
- Avoid inferring missing information
- Avoid extrapolating state
- Avoid automated decision-making
- Surface uncertainty honestly

Violations are consumer defects.

---

## Prohibited Interpretations

The following interpretations are explicitly forbidden:

- “If it’s not there, it didn’t happen”
- “Latest means correct”
- “More entries means more certainty”
- “Chronological implies causal”
- “Missing implies failure”
- “Presence implies success”

Any system relying on these assumptions is incorrect by design.

---

## Governance

This document is subordinate to:

- `THN_CLI_Unified_History_Invariants_Ledger.md`
- `THN_CLI_Unified_History_Field_Contracts_v1.md`
- `THN_CLI_Unified_History_Schema_v1.md`
- `THN_CLI_Unified_History_Temporal_Semantics.md`
- `THN_CLI_Unified_History_Pagination_and_Selection_Semantics.md`
- `THN_Unified_History_Evolution_and_Change_Policy.md`

In case of conflict:
**Invariants → Field Contracts → Schema → Semantics → Non-Guarantees**

---

## Change Policy

Any attempt to introduce a new guarantee requires:

1. Explicit design proposal
2. Versioned documentation
3. Changelog entry (intent and outcome)
4. Cross-review against all Unified History governance documents

Silent elevation of guarantees is prohibited.

---

## Summary

Unified History is:

- Read-only
- Non-inferential
- Non-authoritative
- Partial by design
- Honest about absence

The guarantees it does **not** provide are as important as the ones it does.

End of document.

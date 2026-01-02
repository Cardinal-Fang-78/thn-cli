# THN CLI – Sync Status Contract

## Status
LOCKED (Presentation Contract)

## Purpose

This document defines the authoritative **contract for `thn sync status`**.

It governs:
- Meaning
- Scope
- Interpretation safety
- Consumer expectations

This contract is **presentation-only** and does not alter engine behavior.

---

## Authority Boundary

### Authoritative Source
- **Status DB**
  - Records terminal execution outcomes only
  - Represents completed Sync V2 operations

### Non-Authoritative Sources
- CLI
- Renderers
- Formatting layers
- Downstream consumers

The CLI **does not infer, repair, or reconcile** status data.

---

## Intent of `sync status`

`sync status` answers:

> “What Sync V2 operations have completed, and what was their final outcome?”

It does **not** answer:
- What *should* happen next
- Whether an operation is safe to retry
- Whether remediation is required
- Whether a system is “healthy”

---

## Output Semantics

### Authoritative Fields
These reflect terminal execution outcomes as recorded:

- Operation identifiers
- Timestamps
- Final state (success / failure / noop)
- Target references
- Immutable metadata written at execution time

These fields MAY be used for:
- Reporting
- Auditing
- Display
- Historical review

---

### Diagnostic / Observational Fields

These fields exist to aid understanding only:

- Supplemental notes
- Contextual hints
- CLI-added presentation structure

They MUST NOT be used for:
- Automation
- Policy decisions
- Enforcement
- Gating logic

---

## Screenshot Safety

### Screenshot-Safe Content
Fields that may be shared externally:

- Operation ID
- Timestamp
- High-level outcome
- Target name
- Non-sensitive summaries

### Not Screenshot-Safe
Fields that may expose:

- Internal paths
- Environment-specific details
- Diagnostic internals
- Partial or misleading context

Consumers MUST assume screenshots are **non-authoritative representations**.

---

## Decision Safety

The following is explicitly forbidden:

- Treating `sync status` output as policy input
- Using CLI output to infer future behavior
- Automating retries or remediation based on status alone

All decisions must reference **engine contracts**, not CLI presentation.

---

## JSON Output Contract

- JSON output is deterministic
- Fields are stable once locked
- No inferred fields are permitted
- Presentation labels MAY be added without semantic meaning

Optional forward-compatibility:
- JSON outputs MAY include a top-level `scope` field declaring interpretation intent

---

## Non-Goals

This contract explicitly excludes:

- Live state inspection
- Progress reporting
- Predictive analysis
- Health scoring
- Enforcement semantics

---

## Change Policy

Any change that:
- Alters field meaning
- Introduces inference
- Expands authority

REQUIRES:
- Contract revision
- Golden test updates
- Explicit versioning

---

## Summary

`thn sync status` is:

- Read-only
- Authoritative only for completed outcomes
- Presentation-safe
- Automation-hostile by design

This boundary is intentional and permanent.

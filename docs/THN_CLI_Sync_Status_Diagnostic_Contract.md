# THN CLI — Sync Status Diagnostic Contract

## Status
LOCKED — DIAGNOSTIC SURFACE

---

## Purpose

This document defines the **diagnostic contract** for the
`thn sync status` command.

`sync status` provides a **read-only, observational summary**
of previously recorded Sync V2 execution outcomes.

It exists to support:
- Human inspection
- Debugging
- Reporting
- GUI and tooling consumption

It does **not** participate in execution, policy enforcement,
or decision-making.

---

## Authority Boundary

`thn sync status` operates strictly at the **diagnostic layer**.

| Layer | Role |
|-----|-----|
| Sync V2 engines | Execute operations (authoritative) |
| Status DB | Record terminal outcomes (authoritative history) |
| TXLOG | Record execution lineage (diagnostic) |
| `sync status` | Summarize history (diagnostic-only) |

The command **does not mutate state** and **does not infer correctness**.

---

## Interpretation Rules

### What this command IS

- A read-only view over **historical execution outcomes**
- A diagnostic summary of known Sync V2 activity
- A presentation surface for tooling and UI layers

### What this command IS NOT

- A validator
- A policy gate
- A readiness signal
- An execution prerequisite
- A “safe to proceed” indicator

---

## Field Classification

Output fields produced by `sync status` fall into one of the following categories.

### 1. Authoritative Historical Facts

These fields reflect **engine-committed outcomes** that occurred in the past.

Examples:
- Transaction identifiers
- Timestamps
- Targets
- Terminal success or failure flags

Rules:
- These fields are **historically true**
- They remain **read-only**
- They MUST NOT be interpreted as permission or approval

### 2. Diagnostic Summaries

These fields are derived or aggregated for convenience.

Examples:
- Counts
- Rollups
- Simplified status labels
- Grouped or ordered results

Rules:
- Diagnostic-only
- Non-authoritative
- Subject to change
- MUST NOT drive automation or policy

### 3. Presentation Fields

These fields exist solely to support display or UX.

Examples:
- Ordering
- Grouping
- Human-readable labels

Rules:
- Zero semantic meaning
- Non-stable
- Must never be relied upon

---

## Schema Versioning

Where present, `schema_version` identifies the presentation schema
used by the diagnostic surface.

Rules:
- `schema_version` governs output shape only
- It does not alter authority, execution behavior, or policy
- Consumers MUST treat schema changes as presentation-level unless
  explicitly stated otherwise

Absence of `schema_version` is valid for stub or legacy surfaces.

---

## Screenshot Safety

“Screenshot-safe” refers to **literal screenshots**
(e.g., Windows Snipping Tool, documentation captures, tickets).

### Screenshot-safe fields

- Historical timestamps
- Recorded transaction identifiers
- Explicitly labeled diagnostic summaries

### Not screenshot-safe without context

- Generic “OK” or “Healthy” labels
- Implicit success indicators
- Any field that could be misread as authorization

All screenshots **must be understood as diagnostic context only**.

---

## Labeling and Forward Compatibility

Where JSON output is produced, a top-level `scope` field MAY be used
to explicitly declare interpretation intent.

Approved values:
- `authoritative`
- `presentation`
- `diagnostic`

Rules:
- Absence of `scope` is valid
- `scope` MUST NOT alter semantics or behavior
- `scope` MUST NOT appear inside engine-owned authoritative blocks
- `scope` MUST NOT be treated as configuration or enforcement

For `thn sync status`:
- Output SHOULD use `scope: diagnostic`
- Stub or unimplemented states MAY still emit `scope`

---

## Non-Goals

This command does NOT:

- Execute operations
- Enforce policy
- Validate configuration
- Gate future actions
- Repair or reconcile history
- Guarantee correctness

Any such behavior would require a new command and a new contract.

---

## Change Policy

Any change to:

- Field meanings
- Interpretation rules
- Authority boundaries
- Diagnostic classification

Requires:

- Explicit contract revision
- Documentation update
- Review acknowledgment

Silent semantic drift is prohibited.

---

## Summary

`thn sync status` is a diagnostic read surface over authoritative historical
records.

It is safe to observe.
It is safe to document.
It is safe to screenshot.

It is not a decision surface.

---

END OF CONTRACT

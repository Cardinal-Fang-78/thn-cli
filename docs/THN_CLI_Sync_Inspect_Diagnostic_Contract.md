# THN CLI — Sync Inspect Diagnostic Contract

## Status

LOCKED (Documentation-Only Contract)

This document defines **interpretation and usage constraints** for
`thn sync inspect`.  
It does **not** introduce new behavior, enforcement, or output changes.

---

## Purpose

`thn sync inspect` provides a **read-only diagnostic snapshot** of a Sync V2
envelope and its associated metadata.

It exists to:

- Assist developers and operators during inspection
- Surface structural and completeness diagnostics
- Aid debugging and validation workflows

It does **not** define execution authority or policy decisions.

---

## Authority Boundary

### Authoritative

The following remain authoritative:

- Sync engines
- Validation logic
- Apply execution results
- Enforcement decisions
- Policy gating

### Non-Authoritative (Diagnostic Only)

All output from `thn sync inspect` is:

- Observational
- Non-binding
- Non-enforcing
- Subject to change unless explicitly versioned

No field emitted by `sync inspect` may be treated as a pass/fail signal.

---

## Diagnostic vs Structural Fields

### Structural (Safe to Display)

These fields describe **what exists**, not **what should happen**:

- Envelope metadata
- Manifest structure
- File listings
- Declared modes
- Payload presence

These fields are **safe to display, log, and screenshot**.

### Diagnostic (Interpretation Required)

These fields provide **observations**, not decisions:

- Completeness checks
- Validation summaries
- Warnings or anomaly indicators

These fields:

- MUST NOT be used for automation decisions
- MUST NOT be interpreted as authoritative health signals
- MUST NOT gate workflows or user actions

---

## Screenshot Safety

“Screenshot safe” means:

- A human may capture output using tools such as the OS screenshot or snipping tool
- Output may be shared for debugging or support purposes
- Output must not be interpreted as definitive system health

Screenshot safety **does not imply**:

- API stability
- Automation suitability
- Decision-making authority

---

## JSON Output Intent

`sync inspect --json` emits diagnostic JSON only.

Consumers MUST treat all fields as:

- Informational
- Non-contractual unless otherwise versioned
- Subject to extension

Future releases MAY introduce explicit intent labeling or scoped output
without breaking existing consumers.

---

## Forward Compatibility

This contract intentionally allows future evolution, including:

- A separate diagnostic-only subcommand
- Scoped JSON intent labeling
- Clearer separation between structural and diagnostic payloads

No such separation is required today.

Absence of separation is a **deliberate design choice**, not technical debt.

---

## Non-Goals

This contract explicitly excludes:

- Execution gating
- Health scoring
- Policy evaluation
- Remediation guidance
- Automatic repair recommendations

---

## Summary

`thn sync inspect` is a **human-facing diagnostic aid**.

It is safe to:
- View
- Log
- Screenshot
- Share for support

It is unsafe to:
- Automate against
- Use for enforcement
- Treat as authoritative system state

All authoritative decisions remain owned by engines and apply operations.

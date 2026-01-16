# DX-2.x Diagnostics Policy and Invariants

## Status

LOCKED — Declarative Reference Only

This document defines the **invariants, boundaries, and non-goals** of the
DX-2.x diagnostics phase. It does not introduce new behavior and does not
modify runtime semantics.

---

## Purpose

DX-2.x exists to **declare future-facing diagnostic policy surfaces without
activating them**.

Its goals are to:
- Prevent accidental semantic drift
- Make future enforcement explicit and reviewable
- Guarantee diagnostics remain observational-only
- Ensure no policy inference occurs implicitly

This document serves as the **constitutional reference** for all DX-2.x
documentation and implementation.

---

## Scope

DX-2.x governs **diagnostic interpretation only**.

It applies to:
- CLI diagnostic output
- Diagnostic aggregation
- Diagnostic normalization
- Diagnostic strict-mode scaffolding
- Policy downgrade and escalation rules

It does **not** apply to:
- Engine execution behavior
- Sync apply semantics
- Backup logic
- Status DB authority
- Exit codes
- Routing decisions
- Mutation plans
- CDC execution

---

## Core Invariants (Non-Negotiable)

The following invariants are permanently enforced.

### 1. Diagnostics Are Observational Only

Diagnostics may:
- Observe
- Describe
- Report
- Annotate

Diagnostics may **never**:
- Influence execution
- Change control flow
- Modify exit codes
- Block commands
- Trigger retries
- Alter routing
- Affect persistence

---

### 2. No Implicit Policy Activation

No diagnostic policy may activate via:
- Environment variables
- CLI flags alone
- Presence of fields
- Absence of fields
- Version changes
- Consumer behavior
- Default configuration

All policy activation must be:
- Explicit
- Declarative
- Reviewed
- Versioned

---

### 3. Normalization Is a Boundary Operation

Diagnostic normalization:
- Occurs **only** at the final CLI presentation boundary
- Is never performed by producers
- Is never performed by engines
- Is never performed by CDC logic
- Is never persisted

Normalization exists solely to provide **stable consumer shape**, not
semantic interpretation.

---

### 4. Strict Mode Is Inert by Default

DX-2.x strict mode:
- Declares future enforcement semantics
- Performs **no enforcement**
- Emits **no errors**
- Alters **no exit codes**
- Blocks **no execution paths**

Strict mode may only be activated by a future versioned policy decision.

---

### 5. Downgrade and Escalation Are Declarative Only

Downgrade and escalation rules:
- Define interpretation semantics
- Do not trigger behavior
- Do not suppress diagnostics
- Do not promote diagnostics to errors

They exist to document **how diagnostics would be interpreted** if
policy enforcement were later enabled.

---

## Authority Boundaries

| Layer        | Authority |
|-------------|-----------|
| Engine       | Absolute |
| Status DB    | Authoritative terminal record |
| TXLOG        | Diagnostic, best-effort |
| Diagnostics  | Observational only |
| CLI Output   | Presentation only |
| GUI          | Consumer only |

No layer may assume authority beyond its boundary.

---

## Explicit Non-Goals

DX-2.x explicitly does **not**:

- Introduce enforcement
- Change exit codes
- Add retries or aborts
- Alter CDC behavior
- Modify backup semantics
- Interpret missing data
- Repair history
- Infer execution outcomes
- Reconcile TXLOG and Status DB

Absence of behavior is **intentional**, not incomplete.

---

## Relationship to Other DX Phases

### DX-1.x
- Standardized diagnostic structures
- Locked schemas and aggregation
- Established consumer contracts

### DX-2.x
- Declares interpretation policy
- Freezes boundaries
- Prevents silent escalation
- Introduces no runtime changes

### DX-3.x (Future)
- Would introduce enforcement
- Would require versioning
- Would require migration strategy
- Is explicitly out of scope

---

## Change Policy

Any change to the invariants in this document requires:
- Explicit versioning
- Changelog entry
- Documentation update
- Review acknowledgment

Silent changes are prohibited.

---

## Summary

DX-2.x is a **policy declaration phase**, not an execution phase.

Its purpose is to make future decisions:
- Visible
- Auditable
- Non-accidental

The absence of behavior is the guarantee.

---

End of document.

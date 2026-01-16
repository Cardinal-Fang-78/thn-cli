# THN CLI DX-2 Invariants

## Status

LOCKED — Referential Invariants Ledger

This document is a **concrete, implementation-adjacent reference** for the DX-2.x diagnostics phase.

It enumerates **what is frozen today**, **where those guarantees live**, and **what must not change without explicit versioning**.

It does **not** redefine diagnostic policy.

---

## Authority and Relationship

This document is subordinate to and constrained by:

* **DX-2.x Diagnostics Policy and Invariants** (normative, constitutional)

That document defines *why* DX-2 exists and *what must never happen*.

This document defines:

* **Which DX-2 guarantees are currently locked**
* **Where those guarantees are implemented or declared**
* **Which surfaces are inert vs. active**

If a conflict exists, the DX-2.x policy document is authoritative.

---

## Scope

This document applies **only** to diagnostic behavior and interpretation under DX-2.x.

It covers:

* Diagnostic emission
* Diagnostic aggregation
* Diagnostic normalization
* Strict-mode scaffolding
* Downgrade and escalation policy declarations

It does **not** apply to:

* Engine execution
* Sync apply semantics
* Backup behavior
* Status DB authority
* TXLOG persistence
* Exit codes
* Routing or mutation logic

---

## Locked DX-2 Invariants

The following invariants are **non-negotiable** as of this phase.

### DX2‑1: Diagnostics Are Observational Only

Diagnostics:

* Observe execution state
* Describe detected conditions
* Annotate outcomes

Diagnostics **must never**:

* Influence execution
* Change control flow
* Modify exit codes
* Trigger retries or aborts
* Affect routing or mutation
* Write to authoritative state

**Enforcement status:**

* Fully locked
* Golden-test guarded

**Primary references:**

* diagnostics/diagnostics_consumer_contracts.md
* THN_CLI_Contract_Boundaries.md

---

### DX2‑2: No Implicit Policy Activation

No diagnostic policy may activate implicitly via:

* CLI flags alone
* Environment variables
* Field presence or absence
* Version changes
* Consumer behavior

All future policy activation must be:

* Explicit
* Declarative
* Versioned
* Reviewed

**Enforcement status:**

* Locked by absence (no activation surfaces exist)

**Primary references:**

* THN_CLI_Diagnostics_Policy_Escalation.md
* THN_CLI_Diagnostics_Downgrade_Policy.md

---

### DX2‑3: Normalization Is a Presentation Boundary

Diagnostic normalization:

* Occurs **only** at the final CLI presentation boundary
* Is never performed by engines
* Is never performed by producers
* Is never persisted

Normalization exists solely to provide:

* Stable consumer-facing shape
* Forward-compatible schema exposure

It does **not** imply interpretation or enforcement.

**Enforcement status:**

* Locked
* Golden-tested

**Primary references:**

* THN_CLI_Diagnostics_Normalization_Contract.md

---

### DX2‑4: Strict Mode Is Inert

DX-2 strict mode:

* Declares future enforcement semantics
* Performs **no enforcement**
* Emits **no errors**
* Alters **no exit codes**
* Blocks **no execution paths**

Strict mode may only become active under a future, versioned DX phase.

**Enforcement status:**

* Locked as inert

**Primary references:**

* THN_CLI_Diagnostics_Strict_Mode.md
* THN_CLI_Diagnostics_Strict_Enforcement.md

---

### DX2‑5: Downgrade and Escalation Are Declarative Only

Downgrade and escalation rules:

* Define *interpretation semantics*
* Do not trigger behavior
* Do not suppress diagnostics
* Do not promote diagnostics to errors

They exist solely as **documentation for future enforcement decisions**.

**Enforcement status:**

* Locked as declarative

**Primary references:**

* THN_CLI_Diagnostics_Downgrade_Policy.md
* THN_CLI_Diagnostics_Policy_Escalation.md

---

## Authority Boundaries (DX‑2 View)

| Layer       | Authority                     |
| ----------- | ----------------------------- |
| Engine      | Absolute                      |
| Status DB   | Authoritative terminal record |
| TXLOG       | Diagnostic, best-effort       |
| Diagnostics | Observational only            |
| CLI Output  | Presentation only             |
| GUI         | Consumer only                 |

No diagnostic surface may assume authority beyond observation.

---

## Inert vs. Implemented Surfaces

| Surface            | State                            |
| ------------------ | -------------------------------- |
| Diagnostic schemas | Implemented and locked           |
| Aggregation        | Implemented and locked           |
| Normalization      | Implemented at CLI boundary only |
| Strict mode        | Declared, inert                  |
| Downgrade policy   | Declared, inert                  |
| Escalation policy  | Declared, inert                  |
| Enforcement        | Explicitly absent                |

Absence of behavior is **intentional**.

---

## Change Policy

Any change to DX-2 invariants requires:

* Explicit versioning
* Changelog entry
* Documentation update
* Review acknowledgment

Silent or inferred changes are prohibited.

---

## Summary

DX-2.x is a **policy declaration and boundary-freeze phase**.

This document exists to:

* Make invariants explicit
* Prevent accidental activation
* Provide a concrete reference for maintainers

Behavioral absence is the guarantee.

---

End of document.

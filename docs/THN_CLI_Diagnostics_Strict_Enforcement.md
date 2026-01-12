# DX-2.3 — Diagnostics Strict Enforcement Contract

## Status

LOCKED — DESIGN CONTRACT (NO BEHAVIOR)

DX-2.3 formally defines **what diagnostic strict enforcement means** within the THN CLI ecosystem.

This phase introduces **no runtime behavior**, **no enforcement**, **no exit-code changes**, and **no activation paths**.

It exists to permanently prevent ambiguity and accidental coupling in future diagnostics work.

---

## Purpose

DX-2.3 exists to:

* Define the *only* valid interpretation of “strict diagnostics”
* Prevent implicit or partial enforcement
* Ensure strictness can never be inferred from metadata alone
* Provide a safe, versioned foundation for future enforcement work

DX-2.3 is **definitional, not operational**.

---

## Definition of Strict Diagnostics

In THN, **strict diagnostics** mean:

* Diagnostics may actively influence **diagnostic command outcomes only**
* Enforcement applies **only to diagnostics**, never to engines or mutation paths
* Enforcement is explicit, opt-in, and versioned

Strict diagnostics do **not** mean:

* Engine failure
* Automatic repair
* Policy enforcement
* Health scoring
* Command blocking

---

## Enforcement Boundaries

If strict mode is ever implemented, it MUST obey all of the following:

* Enforcement is limited to diagnostic commands
* Non-diagnostic commands MUST NOT be affected
* Engine behavior MUST remain authoritative
* Presentation layers MUST remain non-authoritative

Strict diagnostics may:

* Fail diagnostic-only commands
* Emit non-zero exit codes for diagnostics
* Enforce schema correctness

Strict diagnostics MUST NOT:

* Alter engine execution
* Block unrelated commands
* Rewrite or reinterpret historical diagnostics
* Mutate state

---

## Activation Requirements (Future Only)

Any future strict diagnostics activation MUST:

* Be explicitly opt-in
* Be clearly documented
* Be versioned as a DX phase
* Be covered by contract tests

Valid activation mechanisms (conceptual only):

* Explicit CLI flag (diagnostics only)
* Explicit environment variable (diagnostics only)
* Explicit CI profile

Implicit activation is **forbidden**.

---

## Exit Code Semantics

If strict diagnostics are introduced:

* Exit codes apply only to diagnostic commands
* Exit codes MUST be deterministic
* Exit codes MUST be documented

DX-2.3 defines **no exit-code behavior**.

---

## Relationship to DX-2.1 and DX-2.2

DX-2.3 builds on:

* DX-2.1 boundary-only normalization guarantees
* DX-2.2 inert activation surface declaration

DX-2.3 introduces **no new hooks** and **no new surfaces**.

---

## Non-Goals

DX-2.3 explicitly does not:

* Implement strict mode
* Enable enforcement
* Define downgrade behavior
* Introduce policy logic

---

## Contract Status

LOCKED — DX-2.3

Any future enforcement work requires:

* A new DX phase
* Explicit documentation
* Contract test updates
* Changelog entries describing intent and outcome

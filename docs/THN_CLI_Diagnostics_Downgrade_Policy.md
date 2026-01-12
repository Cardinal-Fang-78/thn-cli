# THN CLI Diagnostics Downgrade & Severity Policy (Deferred)

---

## Purpose

This document defines the **future policy surface** for diagnostic severity,
downgrade, and enforcement semantics in the THN CLI.

It exists to:

* Prevent accidental semantic drift toward enforcement
* Document what is intentionally not happening today
* Provide a clear insertion point for future policy work
* Preserve the non-authoritative nature of diagnostics by default

This document introduces **no runtime behavior**.

---

## Current State (DX-2.0 Baseline)

As of DX-2.0:

* All diagnostics are **observational only**
* Diagnostic errors, warnings, and metadata **do not enforce behavior**
* No diagnostic result influences:

  * Exit codes of unrelated commands
  * Command availability
  * Mutation, repair, or apply semantics
* No downgrade, escalation, or severity policy exists

Diagnostics report what *is*, not what *must be done*.

---

## Severity Is Not Policy

Diagnostic fields such as:

* `errors`
* `warnings`
* `category`
* `severity` (if present)

Are:

* Descriptive only
* Non-authoritative
* Non-enforcing

They do **not** imply:

* Failure
* Health degradation
* Required action
* Policy violation

Consumers must not infer enforcement semantics from these fields.

---

## Downgrade Semantics (Deferred)

A **downgrade policy** refers to treating certain diagnostic conditions
(e.g. structural anomalies, collisions, missing optional fields) as
warnings instead of errors.

### Current Position

* No downgrade rules exist
* All reported diagnostics retain their producer-defined classification
* Classification has **no behavioral impact**

### Rationale

Downgrade rules are inherently **policy decisions**, not diagnostic facts.

Introducing downgrade behavior requires:

* Explicit policy definition
* Versioned documentation
* Contract test updates
* Clear opt-in semantics

None of these conditions are met in DX-2.0, by design.

---

## Activation Surface (Declared, Inert) — DX-2.2

DX-2.2 introduces a **declared but inert activation surface** for future
diagnostic strictness and downgrade behavior.

This phase exists solely to:

* Name the intended control points
* Reserve semantic space for future behavior
* Prevent ad-hoc or accidental activation paths

### Characteristics

The DX-2.2 activation surface:

* Is **non-functional**
* Introduces **no runtime behavior**
* Does **not** alter diagnostic output
* Does **not** affect exit codes
* Does **not** change classification, severity, or aggregation

No code path may rely on this surface during DX-2.2.

### Forward Compatibility Notes

This contract intentionally leaves room for:

* DX-2.3 strict enforcement
* DX-2.4 policy-driven escalation
* GUI-level severity visualization
* CI-specific downgrade presets

No commitment is made.

### Exit Code Policy (Deferred)

DX-2.2 does not define exit code changes.

Exit code enforcement, if any, is deferred to a later DX phase.

---

## Future Policy Layer (Explicitly Additive)

A future DX branch **may** introduce a policy layer that defines:

* Warning vs error classification rules
* Downgrade or escalation mappings
* Contextual interpretation (e.g. CI vs interactive)
* Strict vs tolerant diagnostic modes

If introduced, that layer MUST:

* Be explicitly versioned
* Be opt-in by default
* Never reinterpret historical diagnostics silently
* Never weaken the guarantees in
  `diagnostics_consumer_contracts.md`

---

## Strict Mode (Conceptual Only)

A future **diagnostic strict mode** may include:

* Schema validation
* Severity enforcement
* Exit code coupling (diagnostics only)
* CI-oriented failure signaling

Strict mode:

* Is not implemented
* Is not implied
* Is not partially present
* Must never be enabled implicitly

Strict mode would be a **separate execution path**, not a reinterpretation
of existing diagnostics.

---

## Non-Goals

This document explicitly does **not** define:

* Enforcement rules
* Automatic repair behavior
* Health scoring
* Alerting thresholds
* CI pass/fail criteria

Those concerns belong to future, versioned policy layers.

---

## Relationship to Other Contracts

This document is constrained by:

* `diagnostics_consumer_contracts.md`
* `THN_CLI_Contract_Boundaries.md`
* `ERROR_CONTRACTS.md`

Nothing in this document supersedes or weakens those guarantees.

---

## Status

**DEFERRED — POLICY STUB**

This document is normative only in defining *absence of behavior*.

Any future implementation requires:

* A new DX version
* Updated documentation
* Explicit contract tests
* Changelog entries describing intent and outcome

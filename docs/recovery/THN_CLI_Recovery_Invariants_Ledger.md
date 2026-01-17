# THN CLI Recovery Invariants Ledger

## Status

LOCKED — Declarative Reference Only  
Read-only. No implementation. No activation semantics.

---

## Verification Note

This ledger was verified against a repository-wide audit of recovery- and
repair-adjacent code and documentation as of commit `d67fed1abfb1fa31d122be871aa4134b0fce9d00`.

No recovery surfaces, automatic repair mechanisms, replay engines, inference
paths, or policy-driven restoration logic were found.

Any future discovery of recovery behavior outside this ledger is considered
a defect and must be addressed explicitly.

---

## Purpose

This document defines the **non-negotiable invariants** governing recovery
behavior in the THN CLI.

It exists to:

- Prevent accidental introduction of implicit recovery
- Clearly separate rollback from recovery
- Lock authority boundaries before recovery is ever implemented
- Ensure future recovery work is explicit, reviewable, and versioned

This ledger does **not** implement recovery.  
It defines the rules that any future recovery system must obey.

---

## Scope

This ledger governs:

- Recovery semantics (if ever introduced)
- Repair, restore, replay, or reconstruction behavior
- Interaction with TXLOG and Status DB
- CLI and GUI recovery surfaces (future)

It does **not** govern:

- CDC rollback during apply
- Backup creation or restoration during apply
- Diagnostic interpretation
- Observability or logging
- Engine execution semantics

---

## Core Invariants (Non-Negotiable)

### 1. Rollback Is Not Recovery

Rollback is:

- Execution-local
- Deterministic
- Bounded to the current operation
- Triggered only by failure during apply

Recovery is:

- Cross-execution
- State-reconstructive
- History-aware
- Explicitly **not implemented**

No rollback mechanism may evolve into recovery implicitly.

---

### 2. No Automatic Recovery Exists

The THN CLI MUST NOT:

- Automatically repair state
- Reconstruct files after failure
- Resume partial execution
- Replay historical operations
- Infer intended state from logs or history

All recovery behavior is **absent by design**.

---

### 3. No Inference from Observability Stores

TXLOG and Status DB:

- Must never drive recovery decisions
- Must never be used to infer missing state
- Must never be replayed automatically

Observability is **read-only** with respect to execution.

---

### 4. Recovery Must Be Explicitly Invoked

If recovery is ever introduced, it MUST:

- Be initiated by an explicit command
- Require affirmative user intent
- Never trigger automatically
- Never activate via defaults, flags, or environment variables

Implicit recovery is forbidden.

---

### 5. Recovery Must Be Versioned (Strict Sense)

“Versioned” means:

- The recovery ruleset is named
- The ruleset is immutable once declared
- The ruleset is selected explicitly
- The ruleset is documented before execution

Recovery behavior MUST NOT vary implicitly across versions.

---

### 6. Recovery Must Be Declarative and Auditable

Any recovery attempt MUST:

- Declare its intended actions up front
- Describe scope and limits explicitly
- Emit a complete plan before execution
- Be auditable after execution

Opaque or heuristic recovery is forbidden.

---

### 7. Recovery Must Never Modify History

Recovery MUST NOT:

- Rewrite TXLOG
- Rewrite Status DB
- Repair or reconcile history
- Synthesize missing records

History is observational, not mutable.

---

### 8. Recovery Must Not Affect Authority Boundaries

Recovery MUST NOT:

- Change engine authority
- Alter exit codes implicitly
- Reinterpret diagnostics
- Bypass safety contracts

Authority boundaries remain intact.

---

## Explicit Non-Goals

Recovery (if introduced) will **not**:

- Be automatic
- Be silent
- Be heuristic
- Be best-effort
- Be self-healing
- Be inferred
- Be continuous
- Be background-driven

Absence of recovery is intentional, not incomplete.

---

## Relationship to Other Systems

### CDC Rollback
- Execution-scoped
- Deterministic
- Already implemented
- Not recovery

### Diagnostics (DX-1 / DX-2)
- Observational only
- No mutation authority
- No repair semantics

### Observability (TXLOG / Status DB)
- Read-only consumers
- No reconstruction
- No reconciliation

---

## Change Policy

Any change to this ledger requires:

- Explicit versioning
- Changelog entry
- Documentation update
- Review acknowledgment

Silent changes are prohibited.

---

## Summary

Recovery in the THN CLI is **intentionally absent**.

This ledger ensures that if recovery is ever introduced, it will be:

- Explicit
- Versioned
- Declarative
- Auditable
- Non-heuristic
- Authority-safe

Until then, **no recovery exists** — and that absence is a guarantee.

---

End of document.

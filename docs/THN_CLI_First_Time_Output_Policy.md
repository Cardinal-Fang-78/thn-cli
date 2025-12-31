# THN CLI – First-Time Output Policy

LOCKED (Interpretation & Consumer Safety Policy)

---

## Purpose

This document defines how **first-time CLI outputs** produced by the THN CLI
MUST be interpreted by users, automation, and GUI consumers.

Its purpose is to:

- Prevent inference of authority, enforcement, or policy where none exists
- Lock interpretation semantics before further surface expansion
- Provide a stable reference for future GUI and tooling integrations
- Ensure first impressions of the CLI are accurate, bounded, and safe

This policy governs **interpretation**, not implementation.

---

## Definition: First-Time Output

A **first-time output** is any user-visible CLI output that may be observed
on the first successful execution of a command in a fresh or unfamiliar
environment.

This includes:

- Default command output
- JSON output without explicit diagnostic or strict flags
- `--help` output
- Errors emitted before any state mutation
- Read-only inspection or history commands

This excludes:

- Debug logging
- TXLOG internal records
- Status DB internal storage
- Golden tests and test harness output

---

## Canonical Output Classification Buckets

Every first-time output MUST belong to **exactly one** of the following buckets.

### A. Authoritative Output

Defines truth about system behavior or outcome.

**Characteristics**
- Deterministic
- Contract-locked
- Engine-owned or explicitly delegated
- Safe to rely on for automation or decision-making

**Examples**
- `thn sync apply --json` engine result
- Terminal execution outcomes surfaced from Status DB

---

### B. Presentation Output

Formats or arranges authoritative data for user consumption.

**Characteristics**
- May reorder, paginate, summarize, or annotate
- Must never change semantics
- Must be reversible or ignorable
- Explicitly non-authoritative

**Examples**
- GUI unified history ordering and pagination
- CLI pretty-printing (non-JSON)
- Cursor metadata

---

### C. Diagnostic Output

Observational, best-effort, non-blocking information.

**Characteristics**
- Never authoritative
- Never enforces behavior
- Never affects exit codes
- Absence is valid and non-error

**Examples**
- CDC payload completeness diagnostics
- TXLOG history reads
- Unified history diagnostic surfaces
- Strict-mode findings (future)

---

### D. Policy / Enforcement Output

Explicit rejection, gating, or validation.

**Characteristics**
- Must be explicit and attributable to policy
- Must not be inferred
- Must clearly indicate enforcement context

**Examples**
- Policy-blocked operations
- Schema rejection
- Signature enforcement (future strict mode)

---

## Command Classification (Initial Locked Set)

| Command | Output Classification |
|------|------------------------|
| `thn --help` | Presentation |
| `thn sync apply --json` | Authoritative |
| `thn sync apply` (non-JSON) | Presentation |
| `thn sync history --unified` | Diagnostic |
| GUI Unified History API | Presentation |
| `thn sync inspect` | Diagnostic (see audit note below) |

---

## Non-Inference Rules (Hard Guarantees)

Consumers MUST NOT infer any of the following unless explicitly declared:

- Engine success or failure from diagnostic output
- Policy enforcement from presentation output
- Validation guarantees from inspection output
- Persistence, durability, or correctness from history surfaces
- Enablement or availability from capability declarations

If behavior is not explicitly declared authoritative, it MUST be treated as
non-authoritative.

---

## Labeling and Forward Compatibility

Where JSON output is produced, a top-level `"scope"` field MAY be used
to explicitly declare interpretation intent.

Example value (illustrative only):

    "scope": "authoritative" | "presentation" | "diagnostic"

Rules:
- Absence of `scope` is valid
- `scope` MUST NOT alter semantics
- `scope` MUST NOT appear inside authoritative engine-owned blocks

---

## Audit Note: `thn sync inspect`

`thn sync inspect` is classified as **diagnostic**.

It:
- Provides observational and structural information only
- Does not imply correctness, readiness, or policy acceptance
- Must not be used as a gating or validation signal

A deeper audit of this command is tracked separately and may refine
documentation or labeling, but not authority.

---

## Status

LOCKED — INTERPRETATION POLICY

This document defines how first-time outputs MUST be understood.
Any change to these rules requires explicit policy revision and review.

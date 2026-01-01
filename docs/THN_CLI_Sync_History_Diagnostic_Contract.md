# THN CLI – Sync History Diagnostic Contract
LOCKED (Read-Only Diagnostics)

## Status

LOCKED — DIAGNOSTIC CONTRACT

This document defines the interpretation rules and JSON surface guarantees for:

- `thn sync history` (TXLOG-only mode)
- `thn sync history --unified --json` (Unified History composite mode)
- `thn sync history --unified --strict --json` (Unified + strict diagnostics)

This contract is read-only and does not define engine behavior.

---

## Purpose

`thn sync history` exists to provide a **read-only** diagnostic view over Sync V2 execution lineage and outcomes.

It is designed to:
- Support inspection and troubleshooting
- Provide audit-friendly visibility into what was recorded
- Preserve strong boundaries between:
  - Authoritative execution
  - Diagnostic observability
  - Presentation-only composition

---

## Authority Boundary

### Authoritative
- **Status DB** is authoritative for *terminal execution outcomes* when present.
- Status DB is authoritative for historical facts only (e.g., timestamps, terminal state, outcome fields recorded by the engine).

### Diagnostic (Non-Authoritative)
- **TXLOG** is diagnostic, best-effort, and non-authoritative.
- TXLOG failures or missing entries must never be treated as execution failures.

### Presentation-Only (Non-Authoritative)
- **Unified History** output is a read-only composite that may combine Status DB and TXLOG into a single view.
- Unified output MUST NOT be interpreted as engine state, validation, enforcement, reconciliation, or repair.

---

## Command Surfaces

### 1) TXLOG-only history (legacy surface)
Command:
- `thn sync history`
- Optional: `--json`

Rules:
- Read-only
- TXLOG is diagnostic-only
- Output MAY be incomplete depending on TXLOG availability

### 2) Unified history (JSON-only)
Command:
- `thn sync history --unified --json`

Rules:
- Read-only
- Composite of:
  - Status DB (authoritative terminal facts when present)
  - TXLOG (diagnostic lineage when present)
- No inference, reconciliation, repair, or policy effects

### 3) Unified + Strict diagnostics (JSON-only)
Command:
- `thn sync history --unified --strict --json`

Rules:
- Adds **diagnostic findings only**
- Strict mode:
  - MUST NOT enforce
  - MUST NOT block execution
  - MUST NOT mutate history
  - MUST NOT repair or reconcile records

Strict mode is a stronger diagnostic lens over the same read-only data.

---

## Schema Versioning

Unified history JSON outputs include a top-level `schema_version` field.

Rules:
- `schema_version` governs the **presentation schema** of the unified history output only
- It does **not** describe engine versioning, migration state, or execution compatibility
- Changes to `schema_version` reflect additive or breaking changes to the CLI’s
  unified history JSON surface

Consumers:
- MAY use `schema_version` to select parsers or rendering logic
- MUST NOT infer engine behavior, data completeness, or policy guarantees from it

---

## JSON Interpretation Labeling

Where JSON output is produced, a top-level `scope` field MAY be used to declare interpretation intent.

Approved values:
- `authoritative`
- `presentation`
- `diagnostic`

Rules:
- Absence of `scope` is valid
- `scope` MUST NOT alter semantics or behavior
- `scope` MUST NOT appear inside engine-owned authoritative blocks
- `scope` MUST NOT be treated as configuration or enforcement

For Sync History surfaces:
- TXLOG-only JSON: MAY omit `scope` (legacy compatibility)
- Unified history JSON: `scope` SHOULD be `diagnostic`
- Unified + strict JSON: `scope` SHOULD be `diagnostic`

---

## What MUST NOT Be Inferred

Consumers MUST NOT infer any of the following from history outputs:
- Eligibility to apply, accept drift, migrate, or repair
- Policy compliance or validation
- Future success likelihood
- Authorization or access control decisions
- Completeness guarantees of TXLOG
- Engine-side ordering semantics based on GUI/presentation ordering

History is visibility, not permission or correctness.

---

## Screenshot Safety (Interpretation Safety)

“Screenshot-safe” means:

A field is safe to share externally (e.g., tickets, screenshots, docs) because it:
- Does not imply authority beyond what is stated
- Does not embed secrets by default
- Is not a policy decision surface

By default:
- Unified history output is **diagnostic** and safe to share for troubleshooting,
  provided it does not include sensitive paths or identifiers in your environment.
- Consumers MUST still treat it as **non-authoritative** except where explicitly
  marked as Status DB terminal facts.

If sensitive information becomes a concern later, redaction rules must be introduced
explicitly as a presentation-only contract (not implied).

---

## Forward Compatibility

Future versions MAY add:
- Additional diagnostic blocks (additive only)
- Additional metadata describing sources and availability (additive only)
- Optional pagination controls (presentation-only)

Any breaking change to:
- Existing keys
- Existing meanings
- Existing authority boundary rules

Requires:
- Explicit contract revision
- Version policy review
- Golden test updates where applicable

---

## Change Policy

Allowed without version bump:
- Additive new fields with clear non-authoritative interpretation
- Additive diagnostic blocks under new top-level keys

Not allowed without explicit contract revision:
- Reclassifying authority of existing fields
- Removing or renaming existing keys
- Converting diagnostics into enforcement semantics
- Introducing inference or reconciliation behavior

---

## Contract Summary

- History is read-only.
- Status DB is authoritative for recorded terminal facts.
- TXLOG is diagnostic-only.
- Unified history is presentation-only composition.
- Strict mode is diagnostics only.
- `scope` is optional labeling that must never change behavior.
- `schema_version` governs the unified history presentation schema only.

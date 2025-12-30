# THN Sync: Unified History Strict Mode (Design-Only)

(Compiled: 12/30/2025)

--------------------------------------------

## Scope

This document defines "Strict Mode" for the Unified History read model as a
diagnostic-only semantic contract.

Strict Mode is NOT an execution feature. It is NOT enforcement. It is NOT a
repair system. It is a stronger diagnostic lens over already-collected data.

This phase is design-only:
- No CLI flags are introduced.
- No output shapes are changed for existing surfaces.
- No default behavior changes.
- No execution semantics changes.

## Terms

- Status DB: The authoritative terminal state store for Sync V2 operations.
- TXLOG: Per-operation lineage stream (JSONL) stored under a scaffold.
- Unified History: A composite read model that presents both sources together,
  without reconciliation or inference.
- Strict Mode: A diagnostic mode that computes explicit findings about
  completeness and consistency, without blocking or repairing anything.

## Non-Goals (Hard Constraints)

Strict Mode MUST NOT:
- Block any operation
- Change exit codes for existing commands
- Mutate any files (Status DB, TXLOG, scaffold, envelopes, etc.)
- Reconstruct missing history
- Invent identifiers, ordering, or timestamps
- Reconcile sources into a "single truth"
- Repair partial or malformed TXLOG streams
- Apply policy effects, gating, or acceptance decisions

Strict Mode MAY NOT introduce shims or compatibility hacks to "make it work"
for GUI. GUI is a consumer. Semantics remain owned by the core read model.

## Authority Model (Locked)

Unified History remains a composite container:

- Status DB is authoritative for terminal state.
- TXLOG is authoritative for lineage.
- The composite read model does not attempt to choose between them.

Strict Mode does not alter authority. It only produces findings about each
source and (optionally) cross-surface relationships.

## Output Contract: Strict Diagnostics Block (Future Slot)

Strict Mode introduces a future-only optional block in the Unified History
payload:

"strict_diagnostics": {
  "mode": "disabled" | "enabled",
  "violations": [],
  "warnings": []
}

Rules:
- In relaxed mode (current default), this block MUST either be omitted or
  present with mode="disabled" and empty arrays.
- When Strict Mode is enabled (future), this block MUST be present with
  mode="enabled" and arrays populated deterministically.

No other fields should change meaning between relaxed and strict mode.
Strict Mode only adds diagnostics.

## Findings Taxonomy (Locked)

Strict Mode findings are categorized into:
- violations: deterministic, contract-level issues
- warnings: deterministic, non-blocking quality concerns

Both are diagnostic-only. Neither category blocks execution.

### Finding Object Shape (Locked)

Each finding is a dict with keys:

{
  "code": "<stable_code>",
  "scope": "status_db" | "txlog" | "cross",
  "severity": "violation" | "warning",
  "message": "<human_readable>",
  "details": { ... }          (optional, JSON-serializable)
}

Rules:
- "code" must be stable over time once introduced.
- "scope" identifies the source domain.
- "details" must never include inferred facts. Only observed values.

## Strict Mode Checks (Design List)

This list defines what Strict Mode is intended to evaluate later. It is not an
implementation requirement today.

### Status DB Domain Checks

S-STATUS-001 (warning)
- Condition: status.present == false
- Meaning: no terminal state record currently available

S-STATUS-010 (violation)
- Condition: status.present == true but record is null or non-dict
- Meaning: status surface claims presence but cannot supply a record

S-STATUS-020 (warning)
- Condition: record exists but required core fields are missing (as defined by
  the Status DB contract for "latest status")
- Meaning: record shape may be older, partial, or a forward-compat variant

### TXLOG Domain Checks

S-TXLOG-001 (warning)
- Condition: txlog entries exist with integrity != "complete"
- Meaning: partial lineage is present; strict mode flags it

S-TXLOG-010 (warning)
- Condition: tx_id == "unknown" appears in entries
- Meaning: malformed/unkeyed records exist; identity is not invented

S-TXLOG-020 (warning)
- Condition: entries exist but timestamps cannot be parsed for sorting
- Meaning: ordering is best-effort; strict mode surfaces the limitation

S-TXLOG-030 (violation)
- Condition: history surface reports status OK but entries contain invalid types
  (non-dict) after normalization
- Meaning: normalization contract is violated

### Cross-Surface Checks (No Reconciliation)

Cross checks MUST NOT "decide truth". They only report observed gaps.

S-CROSS-001 (warning)
- Condition: Status DB present == true, but TXLOG history is empty
- Meaning: terminal state exists without local lineage (could be legitimate)

S-CROSS-002 (warning)
- Condition: TXLOG has recent commits but Status DB present == false
- Meaning: lineage exists without terminal status (could be legitimate)

S-CROSS-010 (warning)
- Condition: status.record indicates a target/mode that is absent from TXLOG
  entries currently loaded
- Meaning: local txlog set may not contain relevant files; do not infer missing

## Determinism Rules (Locked)

Strict Mode output must be deterministic:
- Findings must be stable for a given input set.
- Ordering:
  - violations sorted by (code, scope, message)
  - warnings sorted by (code, scope, message)
- No runtime-dependent identifiers
- No timestamps added by strict mode itself

If observed_at exists in TXLOG entries, it remains TXLOG-owned.

## Future Enablement Policy (Explicitly Deferred)

Strict Mode must remain opt-in:
- Either by a CLI flag (example: --strict) on a read-only command, or
- By an environment variable (example: THN_SYNC_HISTORY_STRICT=1)

This is intentionally deferred until:
- Unified history surface has golden coverage
- GUI consumption path exists
- We can lock the strict output in goldens without churn

## Golden Contract Guidance (When Implemented Later)

When Strict Mode is implemented:
- Add goldens for:
  - strict disabled (current default)
  - strict enabled with:
    - empty txlog + no status
    - partial txlog
    - malformed txlog lines
    - status present + missing txlog
- Goldens must lock:
  - strict_diagnostics shape
  - finding object shape
  - ordering rules
  - stable codes

## Summary (Locked)

Strict Mode is a diagnostic lens:
- It never blocks.
- It never repairs.
- It never reconciles.
- It only reports.

It exists to support:
- GUI rendering (warnings/violations)
- CI visibility (optional later)
- Future strict-mode consumers

It does not change the meaning of Status DB or TXLOG.
It only adds explicit findings about observed data.

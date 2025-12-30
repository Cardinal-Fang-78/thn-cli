# THN Sync V2
## TXLOG Contract

---

## Purpose

TXLOG provides diagnostic, append-only observability for Sync V2 operations.

It records what happened, not what should happen, and is explicitly non-authoritative.

TXLOG exists to support:
- Debugging
- Diagnostics
- Auditing
- Human inspection
- Future GUI and tooling

TXLOG must never:
- Control execution
- Gate behavior
- Enforce policy
- Invent identity
- Block apply semantics

---

## Scope

TXLOG is:
- Scaffold-scoped
- Append-only
- Best-effort
- Non-blocking

TXLOG is not a database and not a source of truth.

---

## Storage Location

TXLOG entries are written under:

<scaffold_root>/.thn/txlog/

Each transaction is stored as a single JSONL file:

<op>-<tx_id>.jsonl

Example:

sync_apply-0ec19878b4f94e1bb1450e98c27079ae.jsonl

---

## Transaction Structure

Each TXLOG file contains ordered JSON lines.

Events:
- begin
- commit
- abort

---

## Begin Event

{
  "event": "begin",
  "tx_id": "<uuid>",
  "op": "sync_apply",
  "target": "<destination path>",
  "started_at": "<ISO8601 UTC>",
  "meta": {
    "dry_run": false,
    "mode": "raw-zip",
    "target": "cli",
    "destination": "<path>"
  }
}

---

## Commit Event

{
  "event": "commit",
  "tx_id": "<uuid>",
  "op": "sync_apply",
  "target": "<destination path>",
  "at": "<ISO8601 UTC>",
  "summary": {
    "outcome": "OK",
    "mode": "raw-zip",
    "target": "cli",
    "destination": "<path>",
    "backup_created": true,
    "backup_zip": "<path>"
  }
}

---

## Abort Event

{
  "event": "abort",
  "tx_id": "<uuid>",
  "op": "sync_apply",
  "target": "<destination path>",
  "at": "<ISO8601 UTC>",
  "reason": "<string>",
  "error": "<string>"
}

---

## tx_id Semantics

- Generated per operation
- Opaque identifier
- No ordering semantics
- Never inferred or reconstructed

Missing begin or commit indicates a partial transaction.

---

## Failure Guarantees

TXLOG must never:
- Interrupt apply
- Raise exceptions to callers
- Change execution flow

TXLOG failures are silently ignored.

---

## Contract Status

LOCKED — DIAGNOSTIC INFRASTRUCTURE

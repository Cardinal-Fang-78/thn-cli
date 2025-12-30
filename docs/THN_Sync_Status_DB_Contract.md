# THN Sync V2
## Status DB Contract

---

## Purpose

The Status DB records authoritative execution history.

It tracks what did happen after execution completes.

---

## Authority Model

Component responsibilities:
- Engine executes
- TXLOG observes
- Status DB records outcomes

Status DB never controls execution.

---

## Storage

SQLite database located at:

<THN_SYNC_ROOT>/status/sync_status.db

---

## Write Semantics

Writes occur:
- After successful execution
- After rollback
- Never during speculative or inferred operations

Writes are explicit.

---

## Read Semantics

Reads return historical facts only.

No prediction.
No inference.
No reconstruction.

---

## Relationship to TXLOG

TXLOG and Status DB are independent:
- Either may exist without the other
- No cross-dependence allowed
- No reconciliation logic permitted

---

## Contract Status

LOCKED — AUTHORITATIVE HISTORY

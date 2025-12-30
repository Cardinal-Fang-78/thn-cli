# THN Sync V2
## Status DB Read Surface

---

## Purpose

Defines the read-only diagnostic surface for the Sync V2 Status DB.

This surface exists to:
- Expose authoritative execution records
- Support diagnostics and inspection
- Reserve naming and intent before future expansion

This surface does **not** participate in execution.

---

## Authority Model

Status DB is authoritative **only** for historical facts.

The read surface:
- Reads completed records only
- Never influences execution
- Never reconstructs state
- Never infers outcomes

---

## Read Semantics

Reads return:
- Stored rows exactly as written
- No derived fields
- No reconciliation with TXLOG
- No filesystem inspection

If data is missing, it remains missing.

---

## Scope

The read surface may expose:
- Apply operation records
- Success or rollback outcomes
- Timestamps as recorded
- Destination and target identifiers
- Stored notes and metadata

The read surface may **not** expose:
- Live state
- Predicted outcomes
- Execution planning
- Cross-source correlation

---

## Relationship to TXLOG

TXLOG and Status DB are independent.

- TXLOG = diagnostic event stream
- Status DB = authoritative outcome record

The read surface must not:
- Merge TXLOG and Status DB
- Compare or reconcile records
- Assume consistency between them

---

## Failure Handling

If the Status DB is unavailable:
- Reads return an explicit error payload
- No fallback to other sources is permitted

---

## Future Evolution

Possible future additions (non-binding):
- Pagination
- Time-range filtering
- GUI-oriented summaries

All future additions must remain:
- Read-only
- Non-authoritative
- Non-inferential

---

## Contract Status

LOCKED — READ-ONLY DIAGNOSTIC SURFACE

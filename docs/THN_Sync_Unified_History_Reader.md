# THN Sync V2
## Unified History Reader

---

## Purpose

The Unified History Reader provides a read-only diagnostic view over TXLOG entries.

It aggregates TXLOG files into structured summaries without interpreting execution semantics.

---

## Source of Truth

Reads only from:

<scaffold_root>/.thn/txlog/*.jsonl

It does not read:
- Status DB
- Filesystem state
- Snapshots
- Registry data

---

## Aggregation Rules

Each TXLOG file is processed independently.

Transaction integrity classification:
- complete: begin and commit present
- partial: begin present, commit missing
- unknown: malformed or incomplete

No inference is performed.

---

## Output Model

Example:

{
  "status": "OK",
  "history": [
    {
      "tx_id": "0ec19878b4f94e1bb1450e98c27079ae",
      "op": "sync_apply",
      "target": "<path>",
      "started_at": "<timestamp>",
      "ended_at": "<timestamp>",
      "outcome": "commit",
      "integrity": "complete",
      "summary": { }
    }
  ],
  "count": 1,
  "truncated": false
}

---

## Filtering

Supported filters:
- limit
- tx-id
- target

Filtering is string-based only.

---

## Unknown Transactions

Transactions without identity remain:

{
  "tx_id": "unknown",
  "integrity": "partial"
}

No numbering or renaming occurs.

---

## Contract Status

LOCKED — READ-ONLY DIAGNOSTICS

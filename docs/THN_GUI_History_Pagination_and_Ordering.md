# THN GUI Unified History – Pagination & Ordering Contract

Status: Locked (Read-Only Contract)
Scope: GUI Consumption Only
Authority: CLI / Core Read Models

---

## Purpose

This document defines the **presentation-level contract** for pagination and
ordering of the **GUI-facing unified sync history**.

It intentionally does **not** redefine engine behavior, storage layout, or
authoritative execution semantics.

---

## Authoritative Principles

• Read-only
• Deterministic
• Stable ordering
• No inference or mutation
• Future-safe (no premature constraints)

The CLI and core read models remain authoritative.

---

## Ordering (Mandatory)

### Default Ordering

Entries are ordered **newest → oldest**.

This is the **only guaranteed ordering** at present.

### Ordering Keys

Ordering is applied using the following precedence:

1. `observed_at` timestamp (preferred)
2. Fallback: txlog file order (stable, deterministic)

If `observed_at` is absent, ordering MUST remain stable across calls.

### Stability Guarantee

Given identical inputs:
- Ordering MUST NOT reshuffle
- Pagination MUST remain consistent
- Repeated calls MUST yield identical sequences

This is a **presentation contract**, not an engine rewrite.

---

## Ordering Direction (Future-Safe Extension)

### Current State

• Ordering direction is **not configurable**
• No CLI flag exists
• No GUI inference is allowed
• Consumers MUST assume newest → oldest

### Forward Compatibility (Explicitly Allowed)

Future versions MAY introduce:
- GUI-only ordering reversal (e.g. oldest → newest)
- Explicit query parameters (e.g. `order=asc|desc`)
- Column-based sort toggles in GUI layers

Consumers MUST NOT assume ordering direction is immutable.

No test or contract enforces irreversible ordering.

---

## Pagination

### Parameters

• `limit` – maximum number of entries to return
• Default: 50
• Minimum enforced: > 0

Pagination is **count-based**, not cursor-based.

### Behavior

• Entries are ordered first
• Pagination is applied second
• No cursor, offset, or page token is exposed
• No filtering beyond delegated query parameters

---

## Non-Goals (Explicit)

• No cursor pagination
• No offset-based paging
• No GUI-side filtering
• No inference of strictness or validation
• No mutation of history records
• No schema evolution enforcement here

---

## Consumer Rules (GUI)

GUI consumers:
• MUST treat output as authoritative
• MUST NOT infer missing fields
• MUST NOT re-sort unless explicitly enabled in a future contract
• MUST tolerate future ordering-direction options

---

## Change Policy

Any change to:
• default ordering
• ordering keys
• pagination semantics

Requires:
• Contract update
• Golden test update
• Versioned documentation entry

---

End of contract.

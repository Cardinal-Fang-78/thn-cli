# THN GUI – Unified History Cursor & Continuity Contract

## Status
LOCKED (Presentation Contract)

## Scope

This document defines the **GUI-only continuity contract** for
Unified Sync History pagination across refreshes.

This contract applies to:
- `thn_cli/ui/history_api.py`
- GUI consumers of Unified Sync History

It does **not** apply to:
- Core history read models
- TXLOG storage or semantics
- Status DB semantics
- CLI behavior
- Engine execution or validation

---

## Purpose

Offset-based pagination alone is insufficient for stable GUI history
navigation when:

- New history entries appear
- History refreshes mid-session
- The user scrolls or pages incrementally

This contract introduces a **presentation-only cursor descriptor**
to preserve continuity **without mutating or inferring authoritative data**.

---

## Authority Boundaries

| Layer | Responsibility |
|------|---------------|
| Core read models | Produce authoritative but unordered data |
| GUI history API | Apply ordering, pagination, and cursor derivation |
| GUI consumers | Treat cursor as opaque and reversible |

The cursor MUST NEVER be interpreted as engine state.

---

## Cursor Descriptor (Presentation-Only)

### Definition

A cursor is a **derived, opaque descriptor** generated from
the last entry of a paginated result.

It MAY include:
- `observed_at`
- `tx_id`
- stable index fallback

It MUST NOT:
- Be persisted automatically
- Be required for basic pagination
- Affect authoritative data
- Imply causality or execution order

---

## Cursor Shape (Recommended)

```json
{
  "cursor": {
    "observed_at": "2025-01-01T12:34:56Z",
    "tx_id": "abc123",
    "fallback_index": 42
  }
}

# THN GUI – Unified History Pagination & Ordering Contract

## Status
LOCKED (Presentation Contract)

## Scope

This document defines the **GUI-only presentation contract** for
ordering and pagination of Unified Sync History entries.

This contract applies to:
- `thn_cli/ui/history_api.py`
- GUI consumers of Unified Sync History

It does **not** apply to:
- Core read models
- TXLOG storage
- Status DB semantics
- CLI authoritative behavior

---

## Authority Boundaries

| Layer | Responsibility |
|------|---------------|
| Core read models | Produce unordered, authoritative data |
| GUI history API | Apply ordering & pagination for presentation |
| GUI consumers | Render results without inference |

Ordering and pagination **must never** be inferred as engine semantics.

---

## Ordering Contract (Mandatory)

### Default Ordering
- **Newest → Oldest**
- This is the default presentation order.

### Reversible Ordering
- GUI consumers may request **Oldest → Newest**
- Reversal is presentation-only and reversible at any time.

### Ordering Keys
1. `observed_at` (preferred, if present)
2. Stable fallback to original TXLOG order

### Stability Guarantee
- Ordering is **stable**
- Identical inputs must produce identical ordering
- No reshuffling between calls with the same parameters

---

## Pagination Contract

### Pagination Model
- Offset-based pagination
- Applied **after ordering**

### Parameters
- `limit`: maximum entries returned
- `offset`: starting index after ordering

### Guarantees
- Pagination does not mutate or truncate authoritative data
- Pagination is deterministic
- Pagination does not affect ordering semantics

---

## Explicit Non-Goals

This contract explicitly forbids:

- Reordering at the engine or TXLOG layer
- Cursor-based pagination (future consideration only)
- Any inference of causality, validation, or strictness
- Any mutation of stored history

---

## Rationale

The ordering and pagination model mirrors established
user expectations (e.g., file explorers, log viewers)
while preserving strict architectural separation between:

- Data authority
- Presentation concerns
- Future extensibility

This prevents premature coupling and preserves long-term
maintainability.

---

## Change Policy

Any change to this contract requires:
- Documentation update
- Explicit test updates
- Versioned acknowledgement

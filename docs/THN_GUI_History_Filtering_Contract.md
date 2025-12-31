# THN GUI – Unified History Filtering Contract

## Status
LOCKED (Presentation Contract)

## Scope

This document defines **GUI-only filtering semantics** for the
Unified Sync History API.

This contract applies to:
- `thn_cli/ui/history_api.py`
- GUI consumers of Unified Sync History

It does **not** apply to:
- Core read models
- TXLOG storage
- Status DB semantics
- CLI authoritative behavior
- Strict-mode evaluation

---

## Authority Boundaries

| Layer | Responsibility |
|------|---------------|
| Core read models | Produce authoritative, unfiltered data |
| GUI history API | Apply presentation-only filtering |
| GUI consumers | Render filtered results without inference |

Filtering must never be interpreted as engine-level semantics.

---

## Filtering Contract (Presentation-Only)

### Supported Filters (Initial)

The following filters are supported:

- `target`
- `tx_id`

These filters are delegated to the read layer when supported, but
their **presentation behavior** is locked by this contract.

---

## Filtering Rules

- Filtering is **opt-in**
- Filtering is **read-only**
- Filtering is **deterministic**
- Filtering is **stable**

Filtering is applied:
1. After unified history read
2. Before ordering
3. Before pagination

---

## Empty Result Handling

If filtering matches no entries:

- The result is still valid
- `history.entries` may be empty
- `history.count` reflects the filtered result
- Top-level shape is preserved

Empty results must never be treated as errors.

---

## Stability Guarantee

Identical inputs MUST produce identical filtered outputs.

Filtering must not:
- Reorder entries
- Mutate authoritative blocks
- Affect cursor semantics
- Affect pagination behavior

---

## Explicit Non-Goals

This contract explicitly forbids:

- Regex or fuzzy matching
- Cross-field inference
- Engine-level filtering
- Cursor mutation
- Pagination inside filters
- Strict-mode interpretation

---

## Rationale

Filtering is a **presentation concern**, not a data authority concern.

This separation:
- Preserves architectural clarity
- Prevents premature coupling
- Enables future extensibility without refactors

---

## Change Policy

Any change to this contract requires:
- Documentation update
- Explicit test updates
- Versioned acknowledgement

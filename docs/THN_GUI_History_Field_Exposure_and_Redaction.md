# THN GUI – Unified History Field Exposure & Redaction Contract

## Status
LOCKED (Presentation Contract)

## Scope

This document defines **GUI-only field exposure and redaction rules**
for Unified Sync History entries.

This contract applies to:
- `thn_cli/ui/history_api.py`
- GUI consumers of Unified Sync History

It does **not** apply to:
- Core read models
- TXLOG storage
- Status DB semantics
- CLI authoritative behavior
- Strict-mode enforcement

---

## Authority Boundaries

| Layer | Responsibility |
|------|---------------|
| Core read models | Produce full authoritative records |
| GUI history API | Control which fields are exposed |
| GUI consumers | Render exposed fields only |

Field exposure is a **presentation concern**, not an authority concern.

---

## Field Exposure Contract

### Default Behavior

- All fields returned by the core reader are passed through unchanged
- No fields are removed by default
- No fields are inferred, synthesized, or renamed

This preserves forward compatibility.

---

## Redaction Rules (Optional, Presentation-Only)

Redaction MAY be applied by the GUI API when enabled in the future.

If redaction is applied:

- Redacted fields MUST be removed entirely
- Redaction MUST NOT replace fields with placeholders
- Redaction MUST NOT alter unrelated fields
- Redaction MUST be deterministic

---

## Stability Guarantees

- Field presence is stable for identical inputs
- Redaction does not affect:
  - Ordering
  - Pagination
  - Cursor semantics
  - Authoritative blocks

---

## Explicit Non-Goals

This contract explicitly forbids:

- Conditional redaction based on content semantics
- Inference of sensitivity
- Role-based filtering
- Partial masking (e.g., `***`)
- Engine-level redaction
- Strict-mode interpretation

---

## Rationale

Field exposure control is required for:
- GUI safety
- Future privacy controls
- Tenant-specific UI views

By locking this as presentation-only:
- Core contracts remain stable
- Future UI policy can evolve safely
- Backward compatibility is preserved

---

## Change Policy

Any change to this contract requires:
- Documentation update
- Explicit test updates
- Versioned acknowledgement

# THN GUI – Unified History Capability Declaration Contract

## Status
LOCKED (Presentation Contract)

## Scope

This document defines the **GUI-only capability declaration contract** for the
Unified Sync History surface.

This contract applies to:
- `thn_cli/ui/history_api.py`
- GUI consumers of Unified Sync History

It does **not** apply to:
- Core read models
- TXLOG storage
- Status DB semantics
- CLI authoritative behavior

---

## Goal

Provide a single, stable way for GUI clients to discover which optional
presentation features are supported by the current backend build, without
guessing based on missing fields, ordering behavior, or version strings.

---

## Contract

### Top-level Optional Block

The unified history result **may** include a top-level field:

- `capabilities` (optional)

If `capabilities` is present:
- It MUST be a JSON object (dictionary)
- It MUST be JSON-serializable
- It MUST NOT replace or mutate authoritative blocks:
  - `schema_version`
  - `status`
  - `history`

Absence of `capabilities` is always valid.

---

### Capability Values

If present, each entry in `capabilities`:

- MUST use a **string key**
- MUST use a **boolean value**

Capabilities are **declarative feature flags only**.

Example:

```json
{
  "capabilities": {
    "ordering": true,
    "offset_pagination": true,
    "cursor_pagination": false,
    "filter_target": true,
    "filter_tx_id": true,
    "field_redaction": false
  }
}

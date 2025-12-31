# THN GUI – Unified History Contracts Index

## Status
LOCKED (Presentation Contracts)

## Purpose

This document is the **single authoritative index** for all GUI-facing
Unified History presentation contracts.

It exists to:
- Provide a stable reference for GUI and tooling consumers
- Prevent inference from shape or behavior
- Make future extension additive and non-breaking
- Establish a clear change policy for all listed contracts

This index is **presentation-only** and does not define engine behavior.

---

## Authority Boundary

| Layer | Responsibility |
|------|---------------|
| Core engines | Produce authoritative data |
| Unified history read model | Aggregate read-only history |
| GUI history API | Declare presentation contracts |
| GUI consumers | Render based on declared support |

GUI consumers MUST rely only on declared contracts listed here.

No GUI consumer may infer behavior, semantics, validation rules, or policy enforcement beyond what is explicitly declared in the referenced contracts.

---

## Locked GUI History Contracts

The following contracts are **individually locked** and **collectively governed**
by this index.

Any change to a listed contract MUST follow the Change Policy defined in this document.

### 1. API Shape Contract
- **File:** `THN_GUI_History_API_Shape.md`
- **Test:** `test_gui_unified_history_api_shape.py`
- **Guarantees:**
  - Stable top-level JSON shape
  - Presence of `schema_version`, `status`, and `history`
  - No inference or mutation
  - Absence of optional fields is valid unless explicitly stated otherwise

---

### 2. Ordering & Pagination Contract
- **File:** `THN_GUI_History_Pagination_and_Ordering.md`
- **Test:** `test_gui_unified_history_ordering_pagination_contract.py`
- **Guarantees:**
  - Default ordering: newest → oldest
  - Stable ordering for identical inputs
  - Pagination is presentation-only
  - No engine-side reordering implied
  - Pagination does not alter authoritative records

---

### 3. Cursor & Continuity Contract
- **File:** `THN_GUI_History_Cursor_and_Continuity.md`
- **Test:** `test_gui_unified_history_cursor_contract.py`
- **Guarantees:**
  - Cursor is optional
  - Cursor is opaque
  - Cursor does not mutate authoritative blocks
  - Absence of cursor is valid
  - Cursor presence does not imply persistence, durability, or server-side state

---

### 4. Filtering Contract
- **File:** `THN_GUI_History_Filtering_Contract.md`
- **Test:** `test_gui_unified_history_filtering_contract.py`
- **Guarantees:**
  - Filtering is presentation-only
  - Supported filters are explicitly declared
  - No implied enforcement or validation
  - Unknown filters are ignored
  - Filtering does not imply authorization or access control

---

### 5. Field Exposure & Redaction Contract
- **File:** `THN_GUI_History_Field_Exposure_and_Redaction.md`
- **Test:** `test_gui_unified_history_field_exposure_contract.py`
- **Guarantees:**
  - Only explicitly exposed fields may appear
  - Redaction is declarative
  - No inference from missing fields
  - No policy semantics implied
  - Field absence does not imply error, denial, or failure

---

### 6. Capability Declaration Contract
- **File:** `THN_GUI_History_Capabilities_Contract.md`
- **Test:** `test_gui_unified_history_capabilities_contract.py`
- **Guarantees:**
  - `capabilities` is a GUI-facing declaration surface
  - Capabilities may be present and empty
  - If present, capabilities MUST be a JSON-safe dictionary
  - Values, if present, MUST be boolean feature flags
  - Capabilities NEVER mutate authoritative data
  - Capabilities do not imply enablement, enforcement, or availability beyond presentation

---

## Capability Model (Forward Path)

The Unified History API may expose a top-level capabilities object.

This object, if present, serves only as a declarative surface indicating which
optional GUI features are supported by the current implementation.

The capabilities object:
- May be omitted entirely
- May be present as an empty dictionary
- May contain one or more boolean flags
- MUST NOT contain nested objects, arrays, or non-boolean values
- MUST NOT be interpreted as configuration or policy
- MUST NOT be required for correct rendering of baseline history

The absence of a capability flag MUST be treated as false or unsupported by GUI
consumers.

The presence of a capability flag MUST NOT be interpreted as a guarantee of
future availability, persistence, or stability beyond the current contract
version.

Capabilities exist solely to allow additive, non-breaking GUI evolution.

---

## Contract Versioning and Stability

All contracts listed in this index are locked at the presentation layer.

This means:
- Existing fields may not be removed
- Existing meanings may not be changed
- Existing defaults may not be inverted
- Existing optionality may not be tightened

Additive changes are permitted only if:
- They are explicitly documented
- They do not alter existing behavior
- They do not require inference by consumers
- They are covered by new tests

Any change that violates these rules requires a new contract version and
explicit opt-in by consumers.

---

## Change Policy

This index is the governing document for GUI Unified History presentation
behavior.

Changes fall into three categories:

1. Documentation-only clarification
   - No behavior change
   - No test change required
   - Allowed without version bump

2. Additive extension
   - New optional fields or capabilities
   - New contracts appended to this index
   - Requires tests and documentation
   - Must not affect existing consumers

3. Breaking change
   - Removal or semantic change
   - Tightened requirements
   - Altered defaults
   - Requires a new schema version and explicit migration path

Breaking changes are explicitly disallowed for existing contracts.

---

## Scope and Non-Goals

This index does not define:
- Engine behavior
- Authorization or access control
- Validation rules
- Persistence guarantees
- Performance characteristics
- Storage formats
- Transport mechanisms

All such concerns belong to engine, policy, or infrastructure layers and MUST
NOT be inferred from GUI presentation contracts.

---

## Final Authority Statement

This document is the single source of truth for GUI-facing Unified History
presentation contracts.

If behavior is not declared here or in a referenced contract, it MUST be treated
as unsupported.

Silence is intentional.

Inference is forbidden.

# THN CLI Unified History Schema v1

LOCKED — Design-Only Schema Declaration  
Read-only. Declarative. No runtime effect.

This document declares **Schema Version 1** for the THN Unified History
read model. It does **not** introduce behavior, migration logic, replay,
recovery, enforcement, or execution semantics.

Verified against repository state at commit:
`26560745f143544137a50c2d0a01c7bbc2eb07f3`

---

## Purpose

This document exists to:

- Declare a **stable, named schema version** for Unified History payloads
- Prevent implicit or ad-hoc structural drift
- Provide a reference point for future additive evolution
- Separate **schema identity** from behavior, policy, or enforcement

This schema is **read-only**, **non-inferential**, and **non-operative**.

---

## Non-Goals

This schema does NOT:

- Define replay, recovery, or rollback behavior
- Authorize mutation, inference, or reconstruction
- Imply migration tooling or version negotiation
- Define strict mode behavior
- Define enforcement, validation, or exit-code semantics
- Serve as an execution contract

---

## Schema Identity

- **Schema Name**: Unified History
- **Schema Version**: 1
- **Status**: LOCKED
- **Scope**: Read-only composite history payload
- **Applies To**:
  - CLI unified history (`thn sync history --json`)
  - GUI unified history ingestion
- **Does Not Apply To**:
  - Execution engines
  - Diagnostics engines
  - Recovery systems

---

## High-Level Payload Shape (Informational)

Schema v1 guarantees the presence of a **top-level unified history object**
composed of:

- Authoritative execution records (Status DB)
- Diagnostic execution traces (TXLOG)
- Optional strict diagnostic overlays (read-only, inert)

Exact field layouts remain governed by:
- Unified History Invariants Ledger
- Unified History Introspection Surface Index

---

## Versioning Rules

- Schema versions are **explicit and monotonic**
- Version numbers are declared, not inferred
- A new schema version:
  - MUST be additive
  - MUST NOT reinterpret v1 data
  - MUST NOT imply migration or replay
- Multiple schema versions MAY coexist in documentation
- Runtime negotiation is explicitly out of scope

---

## Related Governance Documents

This schema is governed by and subordinate to:

- `THN_CLI_Unified_History_Invariants_Ledger.md`
- `THN_CLI_Unified_History_Introspection_Surface_Index.md`
- `THN_Unified_History_Evolution_and_Change_Policy.md`

In case of conflict, **invariants take precedence**, followed by
introspection constraints, then schema declaration.

---

## Future Schema Versions

The presence of this document does **not** imply that Schema v2 or later
versions are planned, scheduled, or required.

Any future schema version must be explicitly declared, reviewed, and
locked in a separate document.

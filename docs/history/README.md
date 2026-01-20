# Unified History Documentation

This directory contains authoritative documentation governing the
**Unified History read model** in the THN CLI.

Unified History provides a **read-only, non-inferential composite view**
over multiple observability sources, without introducing reconciliation,
repair, or execution semantics.

---

## Scope

This documentation covers:

- Unified History authority boundaries
- Composition rules for Status DB and TXLOG
- Read-only CLI and GUI ingestion semantics
- Provenance and non-inference guarantees
- Change policy for history interpretation

---

## Explicit Non-Scope

Unified History does **not** cover:

- Engine execution semantics
- Sync apply or CDC mutation behavior
- Rollback logic
- Recovery behavior
- Diagnostics emission or aggregation
- Policy enforcement or escalation

Rollback is not history.  
Recovery is not history.  
Diagnostics are not history.

---

## Key Documents

- **THN_CLI_Unified_History_Invariants_Ledger.md**  
  Non-negotiable invariants governing Unified History behavior and authority.

- **THN_CLI_Unified_History_Introspection_Surface_Index.md**  
  Exhaustive enumeration of all Unified History read surfaces and explicit
  prohibition of replay, recovery, mutation, or execution control.

- **THN_CLI_Unified_History_Schema_v1.md**  
  Design-only declaration of the Unified History read schema identity.
  Defines versioning rules without introducing behavior or migration semantics.

- **THN_CLI_Unified_History_Field_Contracts_v1.md**  
  Field-level meaning and interpretation guarantees for all Unified History payload fields,
  without introducing validation, enforcement, or behavior.

- **THN_CLI_Unified_History_Nullability_and_Absence_Semantics.md**  
  Declarative interpretation rules for absent, null, empty, or partial Unified History data.
  Absence is preserved and never inferred against.

- **THN_CLI_Unified_History_Temporal_Semantics.md**  
  Declarative semantics for timestamps and ordering. Temporal data is descriptive-only
  metadata and must never imply causality, progression, or execution control.

- **THN_Unified_History_Evolution_and_Change_Policy.md**  
  Governs how Unified History semantics may evolve without violating invariants or
  authority boundaries.

- **THN_CLI_Unified_History_Pagination_and_Selection_Semantics.md**  
  Defines pagination, selection, and truncations/bounded-view interpretation semantics for Unified History read surfaces.

---

## Design Intent

Unified History exists to make execution outcomes and diagnostic lineage
**visible without interpretation**.

The absence of inference, repair, or reconciliation is intentional
and contract-locked.

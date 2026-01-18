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

Future documents may include:
- Unified History introspection surface index
- GUI ingestion contracts (if separated)

---

## Design Intent

Unified History exists to make execution outcomes and diagnostic lineage
**visible without interpretation**.

The absence of inference, repair, or reconciliation is intentional
and contract-locked.

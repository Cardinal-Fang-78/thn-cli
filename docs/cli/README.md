# THN CLI Documentation

## Status

LOCKED — Governance Index  
Declarative only. No runtime behavior. No activation semantics.

---

## Purpose

This directory contains **CLI-wide authority and boundary governance**
documents for the THN CLI.

It exists to:

- Declare what CLI commands are allowed to do
- Prevent accidental escalation of command authority
- Lock execution, presentation, and diagnostic roles
- Provide a stable reference for future CLI surface expansion

This directory does **not** document command behavior, flags, or usage.
It documents **authority**, not implementation.

---

## Scope

Documents in this directory govern:

- CLI command authority classification
- Execution vs. read-only vs. diagnostic boundaries
- Prohibited command behaviors
- Cross-cutting CLI invariants that span subsystems

This directory explicitly does **not** govern:

- Unified History semantics (see `docs/history`)
- Diagnostic contracts or strict mode behavior (see `docs/diagnostics`)
- Recovery authority or workflows (see `docs/recovery`)
- Sync or CDC execution behavior (see `docs/syncv2`)
- GUI contracts (see GUI history docs)

---

## Documents

- **THN_CLI_Command_Authority_Boundaries.md**  
  Declares which CLI commands are execution-authoritative, presentation-only,
  or diagnostic-only, and explicitly forbids history-, diagnostic-, or
  strict-mode–driven execution.

- **THN_CLI_Command_Inventory.md**  
  Enumerates the complete, authoritative CLI command surface exposed via
  `thn_cli.commands.__all__`, classifying each command by authority only
  (execution, diagnostic, or presentation) without defining behavior,
  semantics, flags, or output contracts.

---

## Relationship to Other Documentation

This directory is complementary to:

- `docs/history/` — Unified History governance
- `docs/diagnostics/` — Diagnostic policy and invariants
- `docs/recovery/` — Recovery authority and non-goals
- `docs/syncv2/` — Sync V2 execution and mutation plans
- `docs/THN_CLI_Contract_Boundaries.md` — High-level CLI boundary classification

No document in this directory may weaken or reinterpret guarantees declared
in those locations.

---

## Change Policy

Any addition to this directory requires:

- Clear justification for CLI-wide authority relevance
- Explicit non-overlap with existing governance documents
- Changelog entry (intent and outcome)
- Review against Unified History, Diagnostics, and Recovery invariants

Silent changes are prohibited.

---

## Summary

The `docs/cli` directory exists to **lock command authority**, not to explain
how commands work.

If a document does not define *what a command may or may not do*, it does not
belong here.

End of document.

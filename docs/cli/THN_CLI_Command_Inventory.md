# THN CLI Command Inventory

## Status

LOCKED — Declarative Inventory  
Read-only. No runtime behavior. No activation semantics.

---

## Verification Note

This document was verified against the authoritative CLI command registry
and boundary classification code as of commit:

`e12533677df845bfb53478e2171affa826b83d17`

Verification included:

- Exhaustive comparison against `thn_cli.commands.__all__`
- Validation of top-level command coverage
- Cross-check of all explicit path-level overrides in
  `thn_cli/contracts/cli_boundaries.py`
- Confirmation that no CLI command lacks an explicit authority classification
- Confirmation that no undocumented CLI surfaces exist

All commands listed here:
- Are explicitly registered in the CLI
- Have a deterministic authority classification
- Are governed by the Hybrid-Standard CLI boundary registry

Any future command added to the CLI without a corresponding update to this
document and the boundary registry constitutes a defect.

---

## Purpose

This document provides the **complete, authoritative inventory of all THN CLI
commands** exposed via the canonical command registry.

It exists to:

- Enumerate the full CLI command surface
- Declare **authority classification only**
- Prevent silent expansion or drift of the CLI surface
- Provide a stable reference for tooling, audits, and future consumers

This document does **not** describe command behavior, flags, output,
or semantics.

It answers **what commands exist** and **what authority class they belong to** —
nothing more.

---

## Source of Truth

This inventory is derived from and constrained by:

- `thn_cli.commands.__all__` — canonical command exposure
- `thn_cli/contracts/cli_boundaries.py` — authoritative boundary registry

Any discrepancy between this document and those sources constitutes a defect.

---

## Authority Classes

Each command is classified into **exactly one** authority class:

- **Authoritative** — may mutate state
- **Diagnostic** — observational only
- **Presentation** — read-only convenience

Authority classification describes **capability**, not invocation outcome.

---

## Top-Level Command Inventory

The following table enumerates **all top-level CLI commands** exposed by
`thn_cli.commands.__all__`.

| Command | Authority | Notes |
|------|-----------|------|
| `thn accept` | Authoritative | Policy-gated mutation |
| `thn blueprint` | Diagnostic | Observational |
| `thn cli` | Diagnostic | CLI introspection |
| `thn delta` | Diagnostic | Read-only inspection |
| `thn dev` | Diagnostic | Developer tooling |
| `thn diag` | Diagnostic | Diagnostic suite |
| `thn drift` | Diagnostic | Drift analysis |
| `thn hub` | Diagnostic | Hub interaction |
| `thn init` | Diagnostic | Deterministic setup, no execution authority |
| `thn inspect` | Diagnostic | Read-only inspection |
| `thn keys` | Diagnostic | Key inspection |
| `thn list` | Diagnostic | Enumeration |
| `thn make` | Authoritative | Scaffold creation |
| `thn make-project` | Authoritative | Project creation |
| `thn migrate` | Authoritative | Versioned migration |
| `thn plugins` | Diagnostic | Plugin inspection |
| `thn registry-tools` | Diagnostic | Registry inspection |
| `thn routing` | Diagnostic | Routing inspection |
| `thn snapshots` | Authoritative | Snapshot mutation |
| `thn sync` | Authoritative | Leaf overrides exist |
| `thn sync-remote` | Authoritative | Backward-compat alias |
| `thn sync-status` | Diagnostic | Backward-compat alias |
| `thn tasks` | Authoritative | Task orchestration |
| `thn ui` | Presentation | UX surface |
| `thn version` | Presentation | Version info |

---

## Explicit Leaf-Level Overrides

The following command paths override their top-level classification.

| Command Path | Authority | Resolution |
|------------|-----------|------------|
| `thn sync inspect` | Diagnostic | Static |
| `thn sync history` | Diagnostic | Static |
| `thn sync status` | Diagnostic | Static |
| `thn sync make-test` | Diagnostic | Static |
| `thn sync apply` | Authoritative | Static (even under `--dry-run`) |
| `thn sync web` | Dual-mode | Resolver-based |
| `thn web` | Dual-mode | Resolver-based alias |

---

## Verification

This inventory was mechanically derived from:

- `thn_cli/commands/__init__.py` (`__all__`)
- `thn_cli/contracts/cli_boundaries.py`
  - `BOUNDARY_BY_TOP_LEVEL`
  - `BOUNDARY_BY_PATH`
  - Resolver functions

Each listed command has been verified to:
- Exist in the canonical CLI registry
- Have an explicit authority classification
- Contain no implicit defaults or inferred behavior

Any mismatch between this document and the boundary registry
constitutes a defect.

---

## Dual-Mode Commands

Some commands are intentionally **dual-mode** and require runtime resolution
to determine authority.

These commands:

- Are explicitly declared
- Use resolver-based classification
- Are exhaustively listed

No implicit or inferred dual-mode behavior is permitted.

---

## Invariants

This inventory enforces the following invariants:

- Every CLI command is listed exactly once
- Every command has an explicit authority classification
- No command gains authority implicitly
- No undocumented CLI surface may exist
- No semantics are defined or implied here

Authority classification does **not** grant permission to:
- Consult Unified History
- Infer execution success
- Trigger recovery
- Escalate policy
- Enforce strict mode

---

## Relationship to Other Governance Documents

This inventory is governed by:

- `THN_CLI_Command_Authority_Boundaries.md`
- `thn_cli/contracts/cli_boundaries.py`
- `THN_CLI_Unified_History_Invariants_Ledger.md`
- `THN_Recovery_Authority_and_Invariants.md`
- `THN_CLI_DX2_Invariants.md`

This document may not weaken or reinterpret guarantees declared elsewhere.

---

## Change Policy

Any change to this inventory requires:

1. Code update to the authoritative registry
2. Documentation update here
3. Changelog entry (intent and outcome)
4. Review against authority, history, diagnostics, and recovery invariants

Silent changes are prohibited.

---

## Summary

This document exists to **freeze the CLI surface**.

It defines:
- What commands exist
- How they are classified
- Nothing else

Behavior belongs in code.  
Semantics belong in subsystem documentation.

End of document.

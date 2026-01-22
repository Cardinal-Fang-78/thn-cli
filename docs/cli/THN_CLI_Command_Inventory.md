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
| `thn blueprint` | Diagnostic | Blueprint inspection and listing |
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
| `thn migrate` | Authoritative | Versioned migration |
| `thn recover` | Authoritative | Recovery / repair flows |
| `thn plugins` | Diagnostic | Plugin inspection |
| `thn registry-tools` | Diagnostic | Registry inspection |
| `thn routing` | Diagnostic | Routing inspection |
| `thn snapshots` | Authoritative | Snapshot mutation |
| `thn sync` | Authoritative | Path-level authority resolution applies |
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

## Legacy Shims (Non-Commands)

The following modules exist solely for backward compatibility and do **not**
register CLI commands:

| Module | Purpose |
|------|--------|
| `commands_make_project` | Import-safety shim for legacy tooling |

These modules must never appear in help output or authority inventories.

---

## Delta vs Sync Boundary Clarification

`thn delta` is a **top-level diagnostic domain**, not a subcommand of `sync`.

Rationale:
- CDC inspection and manifest analysis are not sync operations
- Delta tooling operates independently of envelope transport
- The boundary prevents semantic coupling between inspection and execution
- Delta tooling must never be treated as a prerequisite, validator, or gate
  for sync execution.
- **Delta commands have no execution authority and no resolver-based escalation paths**

A future `thn sync delta` shape is explicitly rejected.

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

## Mechanical Verification (Non-Authoritative)

This inventory can be mechanically verified against the codebase using
read-only inspection. No runtime execution, mutation, or policy enforcement
is involved.

The authoritative sources for verification are:

- `thn_cli.commands.__all__` — canonical command exposure
- `thn_cli/contracts/cli_boundaries.py` — authority classification

### Verification Procedure

A verification pass MUST perform the following steps:

1. Enumerate all top-level command modules declared in
   `thn_cli.commands.__all__`
2. Resolve the actual argparse-registered command names
3. Compare the resolved command set against the
   **Top-Level Command Inventory** table in this document
4. Resolve authority classification using:
   - `BOUNDARY_BY_TOP_LEVEL`
   - `BOUNDARY_BY_PATH`
   - Explicit resolver functions

### Defect Conditions

Any of the following constitutes a defect:

- A command exists in code but is missing from this inventory
- A command is listed here but does not exist at runtime
- A command resolves to no explicit authority classification
- A mismatch exists between documented and resolved authority

### Tooling Note

A developer-only verification script MAY be used to automate this comparison.
Such tooling is **advisory only** and does not define, alter, or enforce CLI
behavior (see scripts/verify_cli_inventory.py).

This document remains the declarative authority for the CLI surface.

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

## Appendix A — Machine-Generated Registry Snapshot (Non-Normative)

### Status

ADVISORY — Machine-Generated  
Read-only. Not authoritative. Not binding.

---

### Purpose

This appendix is **machine-generated** from the canonical CLI command
registry (`thn_cli.commands.__all__`) at the time of verification.

It exists solely to:

- Provide an automated cross-check against the authoritative inventory
- Detect accidental CLI surface drift
- Support developer tooling, audits, and reviews

This appendix is **non-normative**.

In the event of any discrepancy, the following sources remain authoritative:

- The **Top-Level Command Inventory** table in this document
- `thn_cli.commands.__all__`
- `thn_cli/contracts/cli_boundaries.py`

This appendix must never override or reinterpret those sources.

---

### Generation Metadata

- Generated by: `scripts/verify_cli_inventory.py`
- Source of data: `thn_cli.commands.__all__`
- Mode: Advisory / read-only
- Execution context: Developer tooling only

---

### Canonical Top-Level Registry Snapshot

The following list reflects the **exact set of top-level CLI commands**
registered in the canonical command registry at generation time.

This list is **alphabetically sorted** and intentionally contains
**no authority classification or semantic interpretation**.

- `thn accept`
- `thn blueprint`
- `thn delta`
- `thn dev`
- `thn diag`
- `thn drift`
- `thn hub`
- `thn init`
- `thn inspect`
- `thn keys`
- `thn list`
- `thn make`
- `thn migrate`
- `thn plugins`
- `thn recover`
- `thn registry`
- `thn routing`
- `thn snapshots`
- `thn sync`
- `thn sync-remote`
- `thn sync-status`
- `thn tasks`
- `thn ui`
- `thn version`
- `thn web`

---

### Explicit Exclusions

The following are **intentionally excluded** from this appendix:

- Leaf command paths  
  (e.g. `thn sync apply`, `thn sync inspect`)
- Path-level authority overrides
- Runtime alias resolution
- Legacy shim modules
- Presentation-only routing indirection

All such details are governed elsewhere and must not be inferred here.

---

### Invariants

This appendix enforces the following invariants:

- No CLI command may exist without registry registration
- No registry entry may exist without inventory documentation
- No authority may be inferred from registry presence
- No semantic meaning is implied by ordering or inclusion

This appendix exists for **verification only**.

---

_End of Appendix A_

End of document.

# Diagnostics Documentation

This directory contains **authoritative documentation governing
diagnostic behavior, interpretation, and boundaries** in the THN CLI.

Diagnostics are **observational only**.

They do not affect execution, routing, persistence, or recovery.

---

## Start Here

Key documents include:

- **DX-2.x Diagnostics Policy and Invariants**  
  (`DX-2.x_Policy_and_Invariants.md`)

- **Diagnostics Consumer Contracts**  
  (`diagnostics_consumer_contracts.md`)

- **THN_CLI_DX2_Invariants.md**  
  Locked invariants governing diagnostic normalization, strict mode,
  and policy declaration.

- **THN_CLI_DX2_Introspection_Surface_Index.md**  
  Exhaustive index of all diagnostic- and policy-adjacent surfaces.

---

## Explicit Non-Scope

Diagnostics do **not** include:

- Recovery behavior
- Rollback semantics
- History reconstruction
- Policy enforcement
- Exit-code control

---

## Authority

All diagnostic guarantees are locked by the documents in this directory.

The absence of enforcement is intentional.

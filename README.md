# THN CLI

Internal development CLI for THN projects.

This repository contains the **THN Master Control / THN CLI**, a contract-driven
command-line interface used to coordinate, inspect, and diagnose THN systems.

## Scope and Intent

The THN CLI is:

- A **development and operations tool**
- A **presentation and coordination layer** over engine behavior
- A **contract-governed interface** with explicitly defined output surfaces

The THN CLI is **not**:

- A policy enforcement system
- An execution engine
- A source of inferred or speculative behavior

All authoritative behavior is owned by underlying engines and contracts.
The CLI surfaces those results verbatim or diagnostically, without mutation.

## JSON Output Semantics

JSON output modes (`--json`) are intended for machine consumption and
contract-based integration.

JSON outputs MAY include a top-level `scope` field declaring interpretation intent.

No JSON output implies enforcement, validation, or authority beyond what is
explicitly documented by the originating engine or contract.

## Documentation and Contracts

Authoritative documentation for this repository lives under `docs/`, including:

- Versioning rules and compatibility guarantees
- CLI and engine contract boundaries
- Golden Master specifications for JSON output
- Sync V2 observability, diagnostics, and history models
- GUI-facing presentation contracts (read-only)

Start here:

- `docs/index.md` — documentation entry point
- `docs/THN_Versioning_Policy.md` — authoritative versioning rules
- `docs/THN_CLI_Contract_Boundaries.md` — engine vs CLI responsibility split
- `docs/GOLDEN_MASTER.md` — locked output contracts enforced by tests

## Status

This repository is actively developed and governed by:

- Locked semantic contracts
- Golden tests for externally observable behavior
- Strict separation between authoritative execution, diagnostics, and presentation

Badges below reflect CI and coverage status for the current `main` branch.

![Tests](https://github.com/Cardinal-Fang-78/thn-cli/actions/workflows/tests.yml/badge.svg)
![Coverage](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Cardinal-Fang-78/thn-cli/main/coverage-badge.json)
[![codecov](https://codecov.io/gh/Cardinal-Fang-78/thn-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/Cardinal-Fang-78/thn-cli)

# THN CLI Documentation

Welcome to the official documentation for the **THN Master Control / THN CLI**.

This site provides:

- Versioning policies
- Developer documentation
- Sync V2 negotiation and delta documentation
- CLI usage and command reference
- Automation and build pipelines
- Tenant-aware documentation templates
- Internal engineering standards for THN components
- GUI-facing presentation contracts
- CLI diagnostic interpretation and consumer contracts

---

## Navigation

- **Versioning Policy** → governs compatibility rules
- **Sync V2 Documentation** → delta operations, negotiation flow
- **CLI Contracts** → authority boundaries and diagnostic interpretation
- **GUI Contracts** → presentation-only, non-authoritative GUI surfaces
- **API Documentation** → auto-generated from source
- **PDF Library** → generated documentation exports
- **Templates** → tenant docs, module/project templates

---

## Developer Documentation

Documentation intended for contributors and maintainers of the THN CLI.

Includes:
- Developer-only commands
- Test and golden-test tooling
- Environment diagnostics
- Maintenance utilities

Primary references:

- **THN CLI Developer Tools** — developer-only utility commands  
  (see `DEV_TOOLS.md`)

---

## CLI Contracts

CLI contracts define **interface and interpretation guarantees only**.

They do not define:
- Engine behavior
- Authorization
- Validation
- Persistence
- Policy enforcement

CLI contracts exist to:
- Declare which outputs are authoritative vs diagnostic
- Prevent misuse of human-facing diagnostics as machine truth
- Define screenshot and reporting safety boundaries
- Preserve future extensibility without breaking consumers

Key CLI contract documents include:

- **THN_CLI_Contract_Boundaries.md**  
  Defines authoritative vs diagnostic vs presentation command and field boundaries.

- **Diagnostics Consumer Contracts**  
  (see `diagnostics_consumer_contracts.md`)  
  Defines how diagnostic output may be consumed, interpreted, stored, and evolved
  without enforcement or coupling.

- **THN CLI – Sync Inspect Diagnostic Contract**  
  Governs human-facing diagnostic interpretation for `thn sync inspect`
  and is explicitly **non-authoritative**.

- **THN Recovery Authority and Invariants**  
  Defines the authority boundaries, invariants, and explicit non-goals for
  post-execution recovery behavior. Recovery is declarative only and
  non-operational unless explicitly versioned and introduced in a future phase.

  Recovery behavior is intentionally absent; see `THN_CLI_Recovery_Invariants_Ledger.md`.

---

## Developer Tools

THN provides developer-only utilities under the `thn dev` command group.
These commands are **non-authoritative**, local-only helpers intended for
development, testing, and diagnostics.

### Temp Cleanup

The following command removes all contents of the THN CLI temp root while
preserving the directory itself:

    thn dev cleanup temp

Behavior:

- Deletes files and subdirectories under the resolved temp root
- Honors the THN_TEMP_ROOT environment variable when set
- Is safe to run repeatedly (idempotent)
- Emits JSON output only
- Never deletes the temp root itself

Intended use cases:

- Clearing test artifacts
- Recovering disk space after large sync apply runs
- Resetting local state before running golden tests

---

## GUI Contracts

GUI contracts define **presentation-layer guarantees only**.

They do not define:
- Engine behavior
- Authorization
- Validation
- Persistence
- Policy enforcement

The primary entry point for GUI history behavior is:

- **THN GUI – Unified History Contracts Index**

This index governs all GUI-facing Unified History contracts and is the
single authoritative reference for GUI consumers.

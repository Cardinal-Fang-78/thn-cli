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
- CLI diagnostic interpretation contracts

---

## Navigation

- **Versioning Policy** -> governs compatibility rules
- **Sync V2 Documentation** -> delta operations, negotiation flow
- **CLI Contracts** -> contract boundaries and diagnostic interpretation
- **GUI Contracts** -> presentation-only, non-authoritative GUI surfaces
- **API Documentation** -> auto-generated from source
- **PDF Library** -> generated documentation exports
- **Templates** -> tenant docs, module/project templates

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

The primary diagnostic contract introduced in Phase C is:

- **THN CLI – Sync Inspect Diagnostic Contract**

This document governs **human-facing diagnostic interpretation**
for `thn sync inspect` output and is explicitly **non-authoritative**.

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

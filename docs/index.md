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

---

## Navigation

- **Versioning Policy** -> governs compatibility rules
- **Sync V2 Documentation** -> delta operations, negotiation flow
- **GUI Contracts** -> presentation-only, non-authoritative GUI surfaces
- **API Documentation** -> auto-generated from source
- **PDF Library** -> generated documentation exports
- **Templates** -> tenant docs, module/project templates

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

- **THN GUI - Unified History Contracts Index**

This index governs all GUI-facing Unified History contracts and is the
single authoritative reference for GUI consumers.

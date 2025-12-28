# THN CLI Changelog

This document follows the **Keep a Changelog** format and adheres to **Semantic Versioning**.

---

## [Unreleased]

### Fixed
- Eliminated GitHub CI ruleset ghost required-check deadlocks by separating
  structural branch protection from PR-only CI enforcement.
- Normalized required CI check binding using GitHub-suggested contexts to
  prevent lifecycle mismatch and placeholder check failures.

### Changed
- CI governance hardened with explicit ruleset domain separation to prevent
  invalid evaluation contexts.
- Branch protection semantics clarified and stabilized for long-term
  maintainability and auditability.

---

## [2.0.0] - 2025-12-11

### Added
- Introduced Hybrid-Standard version of THN CLI.
- Added Sync V2 negotiation tools, delta inspector, and routing engine upgrades.
- Added documentation system (MkDocs, PDF export, tenant generator).
- Added build automation for PyPI, TestPyPI, binary builds, release notes,
  coverage, and code analysis.
- Added version planning and governance system.
- Added tenant-aware documentation system and THN Versioning Policy.

### Changed
- Stabilized routing engine behavior.
- Updated blueprint system and template management.
- Improved diagnostic subsystems.

### Fixed
- Minor bug fixes across diagnostics, sync, routing, and blueprint engines.

---

## [0.1.0] - Initial Internal Release

### Added
- Core routing engine.
- Blueprint engine.
- Sync V2 core modules.
- Diagnostics framework.
- Task scheduler.
- Plugin architecture.

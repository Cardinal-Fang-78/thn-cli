# THN CLI Changelog

This document follows the **Keep a Changelog** format and adheres to
**Semantic Versioning**.

---

## [Unreleased]

### Added
- Golden Master specification for Sync V2 JSON output surfaces.
- Contract-level golden tests enforcing Sync V2 apply, dry-run, inspect, and unified history behavior.
- Explicit CDC payload completeness diagnostics for `thn sync inspect`.
- Unified Sync V2 history read surface, including strict diagnostic mode (read-only).

### Changed
- Sync V2 apply (`thn sync apply --json`) output is now strictly declarative and mirrors
  the authoritative engine result without inferred or wrapper-only fields.
- Sync V2 dry-run apply (`--dry-run --json`) contract stabilized and enforced.
- Sync V2 inspect output clarified as diagnostic-only, with CDC diagnostics surfaced
  explicitly and consistently.
- CI governance hardened via strict separation of structural branch protection
  and PR-only quality gates.
- Required CI check naming and binding normalized to prevent lifecycle mismatch
  and unsatisfiable required checks.

### Fixed
- Eliminated GitHub CI ruleset “ghost required-check” deadlocks caused by
  invalid evaluation contexts.
- Removed ambiguity between engine semantics and CLI presentation layers
  in Sync V2 apply, inspect, and history commands.
- Resolved golden-test inconsistencies caused by wrapper-level assumptions.

---

## [2.0.0] - 2025-12-11

### Added
- Introduced Hybrid-Standard version of THN CLI.
- Added Sync V2 negotiation tools, CDC-delta inspector, and routing engine upgrades.
- Added documentation system (MkDocs, PDF export, tenant generator).
- Added build automation for PyPI, TestPyPI, binary builds, release notes,
  coverage, and static analysis.
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

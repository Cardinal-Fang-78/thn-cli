# THN CLI Changelog

This document follows the **Keep a Changelog** format and adheres to
**Semantic Versioning**.

---

## [Unreleased]

### Added
- Locked backup safety contract governing `thn sync apply`, explicitly prohibiting
  recursive or in-destination backup creation.
- Golden safety test enforcing that `thn sync apply --dry-run` is strictly
  side-effect free, including zero backup creation and zero filesystem mutation.
- Explicit documentation of backup-location guarantees and failure behavior
  for Sync V2 apply operations.
- Deterministic default backup root outside the destination tree for Sync V2
  raw-zip apply operations.

### Changed
- Sync V2 apply backup behavior hardened to prevent unbounded disk usage and
  recursive amplification when destinations are large or misconfigured.
- Sync V2 dry-run semantics clarified and enforced as authoritative planning
  output with no filesystem side effects.
- Backup behavior aligned across CLI, test, and CI environments to ensure
  consistent safety guarantees.

### Fixed
- Eliminated a class of failure where Sync V2 apply could exhaust disk space by
  recursively backing up large destination trees.
- Prevented silent backup amplification during long-running or unattended
  apply executions.
- Added regression coverage to ensure future changes cannot reintroduce unsafe
  backup behavior.

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

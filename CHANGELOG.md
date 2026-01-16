# THN CLI Changelog

This document follows the **Keep a Changelog** format and adheres to
**Semantic Versioning**.

---

## [Unreleased]

### Added
- Golden Master specification for Sync V2 JSON output surfaces.
- Contract-level golden tests enforcing Sync V2 apply, dry-run, inspect, and unified history behavior.
- Explicit CDC payload completeness diagnostics for Sync V2 inspect.
- Unified Sync V2 history read surface, including strict diagnostic mode (read-only).
- Authoritative Sync V2 execution history recording via Status DB (write-only),
  completing the Engine → TXLOG → Status DB observability model.
- Locked contract documentation for Sync V2 TXLOG, Status DB, unified history
  reader, and read-semantics placeholder.
- Unified Sync V2 history composite read model combining Status DB and TXLOG
  into a single read-only, non-inferential payload.
- CLI surface for unified history via thn sync history with unified JSON mode (read-only).
- GUI-facing unified history API providing a stable, read-only ingestion surface
  for future UI consumers.
- Strict Mode semantic contract for unified history diagnostics (design-only,
  opt-in, no enforcement).
- Locked diagnostic contracts for Sync V2 CLI read surfaces, including:
  - thn sync inspect (diagnostic-only)
  - thn sync history (TXLOG, unified, and strict modes)
  - thn sync status
- Explicit diagnostic interpretation rules, authority boundaries, and
  screenshot-safety guarantees for all Sync V2 read-only surfaces.
- Optional top-level JSON scope labeling documented for diagnostic
  and authoritative outputs, without altering execution semantics.
- Developer utility thn dev cleanup temp for safe, idempotent cleanup of the THN temp root,
  honoring THN_TEMP_ROOT, with golden-test enforcement and documented behavior.
- CLI boundary classification registry enforcing deterministic command authority classes
  across the full top-level CLI surface, guarded by hardening tests to prevent silent drift.
- Diagnostic-only CLI boundary registry auditing to detect unclassified top-level commands
  without enforcing behavior or blocking execution.
- Canonical error taxonomy and rendering contracts for the THN CLI,
  including stable exit codes, error kind immutability, and forbidden practices.
- Unified diagnostic result model and suite orchestration documentation,
  clarifying diagnostic structure, aggregation semantics, and consumer guarantees.
- Formal documentation of CLI boundary governance, including:
  - Command authority classification model
  - Registry ownership and enforcement responsibilities
  - Loader-time diagnostic auditing (non-blocking)
- Explicit cross-references between:
  - CLI boundary registry
  - Error contracts
  - Diagnostic result model
  to prevent semantic drift across documentation and implementation.
- Diagnostics hardening phase (DX-1.x) completed, including:
  - Locked Hybrid-Standard diagnostic result schema and aggregation semantics.
  - Canonical diagnostic taxonomy (category, scope, severity) documented and stabilized.
  - Golden contract enforcement for `thn diag all` output surface.
  - Explicit compatibility handling for legacy diagnostic flags (e.g. `--json`, no-op).
  - Clear authority boundaries between diagnostic emission, aggregation, and CLI presentation.
  - Centralized diagnostic category normalization at the result boundary,
    guaranteeing stable category exposure without altering diagnostic behavior.
- Diagnostics Normalization Boundary (DX-2.1)
  - Diagnostics normalization is now guaranteed to run **only** at the final
    CLI presentation boundary.
  - Internal diagnostic producers remain unnormalized and non-authoritative.
  - Normalization is dormant by default and probe-gated for testing.
- Diagnostics Strict Mode scaffolding (DX-2.2)
  - Declares an explicit, inert activation surface for future strict diagnostics behavior.
  - No enforcement, downgrade, or exit-code semantics are introduced.
- Introduced a locked JSON output extension point for Sync V2 CLI commands,
  enabling future ASCII-only / pipe-safe emission without changing default behavior.
- Locked DX-2 diagnostics invariants ledger and introspection surface index,
  establishing a single authoritative reference for inert diagnostics policy
  guarantees and future-facing interpretation surfaces.

### DX / Tooling
- Added bounded, diagnostic-only history echo for `thn dev cleanup temp` to improve traceability without affecting behavior.
- Introduced non-destructive `thn dev init` helper to safely recreate expected local development folders.
- Clarified pytest temp directory ownership and lifecycle (ephemeral by design).
- Locked CDC mutation-plan derivation and rollback semantics with stage-aware,
  path-scoped backups enforced by engine-level golden tests.
- Locked Stage 2 CDC-delta apply semantics (chunk-based write/delete),
  including path safety and unrelated-file preservation, enforced by golden tests.
- Locked CDC Stage 2 observability guarantees via golden tests, enforcing:
  - TXLOG emission on successful CDC-delta apply.
  - Absence of speculative or inferred TXLOG records.
- Locked Status DB write policy for CDC Stage 2:
  - Successful applies are recorded as authoritative execution history.
  - Failed CDC Stage 2 applies are explicitly excluded from Status DB writes.
- Enforced Status DB test isolation using per-test Sync roots to prevent
  cross-test contamination and silent observability regressions.

### Changed
- Sync V2 apply (thn sync apply with JSON output) is now strictly declarative and mirrors
  the authoritative engine result without inferred or wrapper-only fields.
- Sync V2 dry-run apply contract stabilized and enforced.
- Sync V2 inspect output clarified as diagnostic-only, with CDC diagnostics surfaced
  explicitly and consistently.
- CI governance hardened via strict separation of structural branch protection
  and PR-only quality gates.
- Required CI check naming and binding normalized to prevent lifecycle mismatch
  and unsatisfiable required checks.
- Sync V2 engine now emits terminal execution outcomes to the Status DB on
  successful apply and rollback, without altering execution semantics.
- Observability boundaries formalized: TXLOG remains diagnostic-only, while
  Status DB is the sole authoritative execution record.
- Formalized and documented the distinction between authoritative,
  diagnostic, and presentation-only Sync V2 CLI outputs, without
  changing runtime behavior.
- Clarified governance separation between:
  - Authoritative engine behavior
  - CLI presentation boundaries
  - Diagnostic and developer tooling
  without altering runtime behavior.
- Updated documentation structure to avoid duplication of command lists,
  deferring all authoritative classification to code-level registries.
- Diagnostic commands standardized to emit normalized Hybrid-Standard payloads,
  independent of CLI flags or presentation mode.
- Clarified and enforced observability responsibility boundaries for CDC Stage 2:
  TXLOG remains diagnostic-only, while Status DB records terminal success only,
  with failure history intentionally excluded.

### Fixed
- Eliminated GitHub CI ruleset “ghost required-check” deadlocks caused by
  invalid evaluation contexts.
- Removed ambiguity between engine semantics and CLI presentation layers
  in Sync V2 apply, inspect, and history commands.
- Resolved golden-test inconsistencies caused by wrapper-level assumptions.
- Restored the thn dev cleanup temp developer command and re-locked its
  golden test to prevent silent regression of temp-root cleanup behavior.

---

## [Next Release] – TBD

### Added
- (Intentionally empty – to be populated at release cut)

### Changed
- (Intentionally empty – to be populated at release cut)

### Fixed
- (Intentionally empty – to be populated at release cut)

Notes:
- This section is a staging scaffold only.
- No release is implied until a version and date are assigned.
- Entries should be moved from [Unreleased] at cut time.

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

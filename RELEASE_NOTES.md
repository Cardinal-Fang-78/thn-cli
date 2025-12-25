# THN CLI  
## Release Notes: Baseline Stabilization Snapshot

(12/23/2025)

---

## Overview

This release represents a **clean, stabilized baseline** for the THN CLI. Core architecture, CI behavior, and development policies are now locked to provide a reliable foundation for continued feature development, documentation expansion, and future releases.

This snapshot is intended as a **reference baseline**, not a feature-heavy release. No user-visible behavioral changes are expected beyond improved determinism, clarity, and development guarantees.

For a version-by-version history of changes, see `CHANGELOG.md`.

---

## Release Status

- Status: Stable baseline
- Intended audience:
  - THN CLI developers
  - CI and test maintainers
  - Early technical reviewers
- Backward compatibility:
  - Preserved relative to prior internal snapshots
  - No breaking CLI surface changes introduced in this release

---

## Python Version Policy (Locked)

The THN CLI now follows a **formal, documented Python support policy**:

- Python 3.12  
  - Primary supported version  
  - Used for CI guarantees, golden tests, and official compatibility claims

- Python 3.14  
  - Forward-compatibility and development validation only  
  - Used during active development to detect upcoming language changes early  
  - Not considered the authoritative compatibility baseline

This policy is intentional and locked to ensure:

- Deterministic CI results
- Stable golden tests
- Clear expectations for contributors and downstream users

---

## CI and Governance Status (CI v1)

This snapshot formally establishes **CI v1** as frozen and authoritative.

- CI surface:
  - Single authoritative CI gate (Python 3.12)
  - All other workflows are advisory or manual by design
- Branch protection:
  - Merge gating limited to the authoritative CI workflow only
  - Linear history enforced
  - Force-pushes restricted
  - Deletions restricted to users with bypass permissions
- Automation guarantees:
  - No silent repository mutation
  - No accidental enforcement through advisory workflows
  - Explicit intent required for all high-impact operations

This establishes a stable and predictable CI and governance foundation for all future development.

---

## CI and Testing Status

CI is considered **stabilized** in this snapshot.

- Continuous integration guarantees:
  - Python 3.12 execution
  - Deterministic test runs
  - Stable, named workflow and job identifiers
- Test coverage status:
  - Core CLI smoke tests passing
  - Routing and entrypoint tests passing
  - Golden tests locked where applicable
- CI philosophy:
  - No simulated workflows
  - No inferred success states
  - Explicit failure on contract violations

This snapshot establishes the CI environment as a **trustworthy signal**, suitable for gating future changes.

---

## Architecture and Codebase State

- Core CLI architecture:
  - Stable and modular
  - Explicit command registration
  - Clear separation between authoritative logic and presentation
- Sync V2:
  - Envelope-based workflows validated
  - Inspect and apply semantics stabilized
  - CDC-delta mode validated where implemented
- Recovery, diagnostics, and future subsystems:
  - Explicitly tracked
  - Intentionally deferred where not yet authoritative
  - No placeholder behavior presented as functional

---

## Development Process Guarantees

This snapshot formalizes several development guarantees:

- No fabricated background processes or implied async behavior
- No simulated recovery, replay, or rollback flows
- Full-file replacements are required for core logic changes
- Structural correctness is prioritized over speed or shortcuts
- Deferred features are documented as intentional design choices, not omissions

These rules are now considered **baseline expectations** for all future THN CLI work.

---

## Documentation and Future Work

- Documentation:
  - Manual-grade documentation is planned and tracked
  - `docs/contributing.md` is now authoritative for contribution and CI rules
- Deferred enhancements:
  - Advanced diagnostics
  - GUI-facing inspection views
  - Extended CDC and signature enforcement
- All deferred items are explicitly tracked and intentionally excluded from this release

---

## Summary

This release establishes a **clean, reliable starting point** for the THN CLI moving forward. With CI governance frozen, Python support clearly defined, and architectural boundaries respected, future development can proceed with confidence and minimal risk of regression.

No additional action is required to adopt this snapshot.

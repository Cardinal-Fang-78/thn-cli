# Contributing to THN CLI

This document defines the **authoritative development and contribution rules** for the THN CLI.  
All contributions must follow these rules to preserve determinism, stability, and long-term maintainability.

---

## Supported Python Versions

The THN CLI follows a **locked Python support policy**:

- **Python 3.12**
  - Primary supported version
  - Authoritative for CI guarantees and golden tests

- **Python 3.14**
  - Forward-compatibility and development validation only
  - Used to detect upcoming language changes early
  - Not an official compatibility baseline

Contributions must not rely on behavior that only works on versions newer than Python 3.12.

---

## CI and Automation Contract

The THN CLI repository follows a deliberately minimal and explicit CI model.

### Authoritative CI

Only one workflow is authoritative and may block merges:

- **THN CLI: CI**
  - Runs on Python 3.12
  - Executes the test suite
  - Must pass for all merges to `main`

No other workflow is permitted to block merges.

### Advisory Workflows

The following workflows provide visibility only and never block merges:

- Extended test matrices
- Nox sessions
- Static analysis (Black, Flake8, MyPy)
- Pre-commit checks
- CodeQL security scans
- Documentation builds

These workflows may:
- Run manually
- Run on a schedule
- Fail without blocking development

Failures are treated as signals, not enforcement.

### Manual / High-Impact Workflows

The following workflows are manual or tag-driven only:

- Publishing to PyPI or TestPyPI
- Building binaries
- Generating release notes or release PDFs
- Updating changelogs
- Generating documentation artifacts

These workflows never mutate the repository automatically and require explicit human intent.

### Design Principles

- No silent repository mutation
- No accidental enforcement
- No implied guarantees
- Recovery paths exist for all automation
- Authority is explicit, not inferred

This contract is considered **stable** unless explicitly revised.

---

## CI and Testing Expectations

- All changes must pass CI without disabling checks.
- CI is treated as an **authoritative signal**, not a suggestion.
- Workflow and job names are stable contracts and must not be renamed casually.
- Simulated success, inferred outcomes, or bypassed failures are not acceptable.

If CI fails, the change is considered incomplete.

---

## Branch and Workflow Expectations

- `main` represents the authoritative, stabilized branch.
- All work is expected to keep `main` in a passing CI state.
- Long-lived divergent branches are discouraged.

Small, incremental commits directly to `main` are acceptable when changes are:
- Well-scoped
- Tested
- Consistent with existing project direction

Larger or exploratory work should be clearly marked and documented.

---

## Branch-Switch Hygiene (Required)

This checklist exists to prevent silent regressions caused by branch switching, conflict resolution, or partial file reconstruction.

These steps are mandatory for all development work.

### Before Switching Branches

Verify the working tree is clean:
- git status

If the working tree is not clean, do one of the following:
- Commit the changes, or  
- Stash them explicitly using:
    - git stash push -u -m "wip before branch switch"

Do not switch branches with uncommitted or partially staged changes.

### After Switching Branches

Immediately verify repository state:
- git status

If any files appear modified unexpectedly, stop and investigate before proceeding.

Open and visually verify safety-critical files when applicable, including but not limited to:
- .gitignore  
- Filesystem utilities (for example fs_ops.py)  
- Developer tooling commands  

Confirm that non-negotiable rules (such as temp directory exclusions and safety guardrails) are still present.

### Before Pushing a Pull Request

Run the full test suite:
- pytest

No exceptions.

After tests pass, create a local backup of the repository state.
This archive is considered authoritative recovery material if a regression is later discovered.

### After Merging a Pull Request

Synchronize local state:
- git checkout main  
- git pull  
- git status  

Re-open and confirm safety-critical files touched by the merge, including .gitignore and any filesystem or tooling utilities.

This step ensures that no branch-switch or merge tooling silently reverted protections.

Failure to follow this checklist is considered a process error, not a tooling error.

---

## Change Scope and File Modification Rules

### Core Logic Changes
- Core and high-impact files require **full-file replacements**.
- Partial edits or snippets are not permitted unless explicitly requested.
- The existing repository state is the source of truth.

### Architectural Decisions
- Prefer solutions with:
  - Lowest long-term maintenance cost
  - Strong future extensibility
  - Clear reuse potential
- Shims, wrappers, and inference-based behavior are disallowed when a structurally correct solution exists.

### Deferred Features
- Deferred functionality must be:
  - Explicitly documented as deferred
  - Excluded entirely from runtime behavior
- Placeholders, stubs, or implied workflows are not permitted.

Deferred by design is not technical debt.

---

## Documentation and Release Artifacts

### CHANGELOG.md
- Records **version-to-version deltas only**
- No policy, baseline, or architectural narration

### RELEASE_NOTES.md
- Represents the **current authoritative baseline**
- Updated as the project state changes

### docs/release-notes/
- Contains immutable, historical snapshot files
- Files in this directory must not be modified once written

---

## Development Philosophy

The THN CLI prioritizes:

- Determinism over convenience
- Explicit behavior over inference
- Structural correctness over short-term speed
- Intentional absence over misleading presence

All contributions are expected to uphold these principles.

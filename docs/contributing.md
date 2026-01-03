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

## Pre-Commit Safety Reminder (Required)

This reminder exists to prevent committing incomplete, mis-scoped, or silently regressed changes.

These checks are mandatory before every commit.

### Before Creating a Commit

Verify repository state:
- git status

Ensure:
- No unexpected file modifications
- No untracked files that should be ignored
- No safety-critical files modified unintentionally

Review all staged changes explicitly:
- git diff --staged

Do not rely on memory, assumptions, or test success alone.

### Required Local Validation

Run the full test suite:
- pytest

Commits must never be created from a failing test state.

If tests were skipped or partially run, the commit is considered invalid.

### Safety-Critical File Confirmation

If any of the following were touched, they must be re-opened and visually confirmed before committing:
- .gitignore
- Filesystem utilities (for example fs_ops.py)
- Backup, temp, or cleanup logic
- Developer tooling commands
- Test fixtures or golden tests

Confirm that safety guarantees, exclusions, and guardrails are still present.

### Commit Intent Check

Each commit must answer all of the following:
- What behavior changed?
- Why is the change necessary?
- What invariant is preserved or strengthened?

If any answer is unclear, do not commit.

Failure to follow this reminder is considered a process error, not a tooling error.

---

## Always-Verify Safety List (Non-Negotiable)

The following files and behaviors are considered safety-critical and must be explicitly verified whenever they appear in a diff, conflict resolution, or branch switch:

- .gitignore
  - Temp directories (for example temp_test) must never be removed from exclusions
  - Build artifacts and local-only directories must remain ignored

- Filesystem utilities
  - Backup logic must never write into destination trees
  - Temp cleanup must never delete the temp root itself
  - Safety refusals and guardrails must remain explicit

- Developer tooling commands
  - Cleanup commands must remain idempotent
  - Developer commands must never mutate state implicitly
  - JSON output contracts must remain stable

- Golden tests
  - Must exist for all safety-critical behaviors
  - Must fail loudly on regression
  - Must not be weakened or removed without versioned intent

If any item on this list is uncertain, development must pause until verified.

---

## Optional Local Pre-Commit Hook (Documentation Only)

A local Git pre-commit hook may be installed to provide an additional safety reminder.
This hook is optional and must never be relied on as enforcement.

### Purpose

The pre-commit hook exists to:
- Warn before committing with a dirty or suspicious state
- Encourage manual verification of safety-critical files
- Reduce reliance on memory during rapid iteration

### Example Behavior (Non-Enforced)

A local hook may:
- Abort commits if tests were not run recently
- Display a reminder to review .gitignore and filesystem utilities
- Prompt for confirmation when safety-critical files are staged

### Important Notes

- The project does not require a pre-commit hook
- No hook is checked into the repository
- CI does not assume a hook exists
- All safety guarantees remain enforced by process and review, not automation

Pre-commit hooks are a local convenience only.

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

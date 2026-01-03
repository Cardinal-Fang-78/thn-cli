# THN CLI — Golden Master Contract

This document defines the **Golden Master behavior contract** for the THN CLI.

Once established, the Golden Master represents the **canonical, externally
observable behavior** of the CLI. Any deviation is considered intentional and
must be explicitly reviewed and approved.

---

## Status

LOCKED — BEHAVIORAL CONTRACT

---

## What the Golden Master Is

The Golden Master is a snapshot-based contract that locks **user-visible CLI behavior**, including:

- Exit codes
- Standard output (stdout)
- Standard error (stderr)
- Error message wording and formatting
- Help, usage, and version output
- JSON output shape and field semantics for contract-governed commands

These behaviors are validated via tests located in:

- `tests/golden/`
- `tests/golden/snapshots/`

---

## What the Golden Master Is Not

The Golden Master does **not** freeze:

- Internal implementation details
- Refactoring choices
- Performance characteristics
- Internal logging or tracing
- Engine internals or non user-visible state
- Filesystem timing or OS-specific performance

Only **externally observable CLI behavior** is covered.

---

## Command Scope and Authority

Golden Master coverage applies only to **CLI-owned presentation surfaces**.

It does not redefine authority:

- Engines remain authoritative for execution
- Status DB remains authoritative for recorded terminal outcomes
- TXLOG remains diagnostic-only
- CLI output reflects, but does not reinterpret, those sources

---

## Sync Apply Semantics (Authoritative)

### Live Apply

`thn sync apply` (without `--dry-run`) reflects the **authoritative engine result**
after execution completes.

Golden tests validate:
- Output structure
- Field presence
- Declarative consistency with engine return values

They do **not** validate:
- Execution duration
- Filesystem performance
- Backup compression speed

---

### Dry-Run Apply

`thn sync apply --dry-run --json` is **authoritative with respect to planning**.

Specifically:
- Routing resolution
- Destination selection
- Mode and operation classification
- Declarative intent of the apply operation

Even though no filesystem side effects occur, the dry-run output is:
- Authoritative for what *would* be executed
- Non-speculative
- Contract-governed and Golden-enforced

Dry-run output must not be treated as diagnostic or advisory.

---

## Modification Rules

Golden snapshots MUST NOT be modified unless **all** of the following are true:

1. A user-visible behavior change is intentional
2. The change is reviewed and justified
3. Snapshots are regenerated explicitly
4. The change aligns with a versioned milestone

Accidental snapshot drift is treated as a regression.

---

## Snapshot Regeneration

To intentionally update Golden Master snapshots:

### Windows (cmd.exe)

    set THN_UPDATE_GOLDEN=1
    pytest tests/golden

To clear after use:

    set THN_UPDATE_GOLDEN=

### Windows (PowerShell)

    $env:THN_UPDATE_GOLDEN = "1"
    pytest tests/golden

To clear after use:

    Remove-Item Env:THN_UPDATE_GOLDEN
    or
    $env:THN_UPDATE_GOLDEN = $null

### POSIX shells
Note: When using the one-line invocation form, the variable is scoped to that command and does not persist.

    THN_UPDATE_GOLDEN=1 pytest tests/golden

To clear after use:

    unset THN_UPDATE_GOLDEN

Snapshot updates MUST be committed alongside the code changes that justify them.
Accidental or implicit snapshot regeneration is prohibited.

---

## CI Enforcement

Golden Master tests are enforced in CI.

Any pull request that changes user-visible behavior without updating
Golden snapshots will fail by design.

This is intentional.

---

## Philosophy

The Golden Master exists to ensure:

- Stable UX guarantees
- Predictable automation behavior
- Safe refactoring over time
- Confidence during long-term evolution

Breaking the Golden Master is a decision, not an accident.

---

END OF CONTRACT

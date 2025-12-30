<!-- Placeholder: to be populated after Pack v3 stabilization -->
# THN CLI Golden Master Specification

## Scope and Purpose

This document defines the **authoritative Golden Master output contracts** for the THN CLI.

It exists to:

* Lock externally observable CLI and engine output surfaces that are enforced by golden tests
* Provide a single, canonical reference for what is guaranteed stable
* Prevent accidental re‑introduction of inferred, simulated, or wrapper‑dependent semantics
* Serve as the contract reference for future CLI, GUI, CI, and documentation consumers

This specification is **normative**. If behavior conflicts with this document, the behavior is incorrect unless this document is deliberately revised.

---

## Authority Model

THN CLI follows a strict authority hierarchy:

1. **Engine contracts** define truth
2. CLI commands adapt engine results for presentation only
3. Golden tests bind to **engine‑level semantics**, not CLI wrappers

Golden tests MUST:

* Assert only documented fields
* Avoid relying on transient CLI formatting or wrappers
* Avoid inferred or computed diagnostics not explicitly declared

---

## Sync V2 Apply — Authoritative Contract

### Entry Point

The authoritative Sync V2 apply path is:

```
thn_cli.syncv2.engine.apply_envelope_v2(envelope, target, dry_run)
```

All CLI commands that apply Sync V2 envelopes delegate to this function.

There are no alternate production apply paths.

---

## Common Apply Result Fields

The apply function returns a **single JSON object**.

The following fields are guaranteed to exist unless otherwise stated.

### Required Fields

| Field         | Type   | Description                                        |
| ------------- | ------ | -------------------------------------------------- |
| `success`     | bool   | Whether the apply operation completed successfully |
| `mode`        | string | Sync mode (`raw-zip` or `cdc-delta`)               |
| `target`      | string | Target name used for apply                         |
| `destination` | string | Absolute destination path                          |
| `routing`     | object | Resolved routing metadata                          |

### Conditional Fields

| Field                     | Present When                   | Description                        |
| ------------------------- | ------------------------------ | ---------------------------------- |
| `operation`               | success == true                | `"apply"` or `"dry-run"`           |
| `applied_count`           | CDC-delta apply                | Declarative count of applied files |
| `files`                   | CDC-delta apply                | Declarative list of files applied  |
| `backup_created`          | apply attempted                | Whether a backup was created       |
| `backup_zip`              | backup_created == true         | Path to backup zip                 |
| `restored_previous_state` | apply failed                   | Whether rollback occurred          |
| `error`                   | success == false               | Human‑readable error summary       |
| `errors`                  | validation or execution errors | List of error messages             |

Fields not listed here are **not guaranteed** and must not be asserted by golden tests.

---

## CDC‑Delta Apply Semantics

CDC‑delta apply reporting is **declarative**, not inferential.

### Declarative Guarantees

* `applied_count` reflects manifest intent, not filesystem diffs
* `files[]` entries are derived from manifest declarations
* Ordering of `files[]` matches manifest order when possible
* No attempt is made to infer change deltas

Example `files[]` entry:

```
{
  "logical_path": "nested/bravo.bin",
  "dest": "C:/THN/projects/Demo/assets",
  "size": 10
}
```

### Explicit Non‑Guarantees

The following are **intentionally excluded**:

* Per‑file diff results
* Payload completeness diagnostics
* Missing/extra file inference
* Filesystem scanning or comparison

These omissions are deliberate to preserve determinism, performance, and test stability.

---

## Dry‑Run Behavior

When `dry_run == true`:

* No filesystem mutation occurs
* No backups are created
* Result indicates intent only

Guaranteed fields:

```
{
  "success": true,
  "operation": "dry-run",
  "mode": "<mode>",
  "target": "<target>",
  "destination": "<path>",
  "routing": { ... }
}
```

Dry‑run results do **not** enumerate per‑file plans. File‑level planning belongs to non‑authoritative tooling.

---

## CLI Wrappers and Status Fields

CLI commands MAY wrap engine results for user presentation.

Examples include:

* Top‑level `status` fields
* Grouping under `apply`, `inspect`, or `diagnostics` keys

These wrappers are **not part of the Golden Master contract**.

Golden tests MUST NOT:

* Assert wrapper fields
* Assume wrapper structure
* Depend on CLI‑only formatting

---

## Versioning and Stability

This specification is version‑agnostic by default.

Any breaking change to:

* Field presence
* Field meaning
* Apply semantics

Requires:

* Explicit revision of this document
* Corresponding golden updates
* Changelog entry documenting the contract change

---

## Summary

This document defines the **only supported Golden Master surface** for Sync V2 apply operations.

It enforces:

* Single authoritative apply path
* Declarative, deterministic reporting
* Clear separation between engine truth and CLI presentation

All future development must preserve these guarantees unless deliberately revised.

# THN CLI Sync Apply Backup Safety Contract

## Status
LOCKED — Safety and Correctness Contract

## Scope

This document defines the mandatory safety guarantees governing filesystem
backups performed by `thn sync apply`.

This contract applies to:
- Raw ZIP apply
- CDC-delta apply
- CLI and test executions
- Local and CI environments

## Core Guarantees

### Dry-Run Safety

When `--dry-run` is specified:

- No backups are created
- No files or directories are modified
- No temporary directories are promoted
- No disk usage growth is permitted

Dry-run is strictly side-effect free.

### Backup Location Safety

Backups MUST NOT be created inside the destination directory tree.

Violations of this rule can cause recursive backup amplification and are
explicitly prohibited.

If a backup directory resolves inside the destination path, the operation
must fail with a clear error.

### Default Backup Location

For raw ZIP apply, backups are created under:  
`<destination_parent>/_thn_backups/sync_apply/`

This location is guaranteed to be:
- Outside the destination tree
- Deterministic
- Non-recursive
- Suitable for large payloads

### Backup Creation Conditions

A backup is created only when:
- The destination path exists
- The destination directory is non-empty
- The operation is not a dry-run

If these conditions are not met, no backup is created.

### Failure Behavior

If backup creation fails:
- The apply operation must fail explicitly
- No partial state may be promoted
- The destination must remain unchanged

Backup failures must never silently degrade into unsafe behavior.

## Non-Goals

This contract does NOT define:
- Backup retention policies
- Compression ratios or performance targets
- User-facing backup configuration flags

Those may be introduced later as opt-in features.

## Rationale

This contract exists to:
- Prevent catastrophic disk exhaustion
- Preserve deterministic apply behavior
- Guarantee test and CI safety
- Ensure operational predictability on large datasets

Backup safety is correctness, not optimization.

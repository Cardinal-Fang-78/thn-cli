# THN CLI Developer Tools

## Purpose

This document describes **developer-only utilities** provided by the THN CLI.

These commands are intended for:
- Local development
- CI and test environments
- Maintenance and diagnostics

They are **not** user-facing runtime features.

---

## CLI Inventory Verification

A developer-only verification tool is available to ensure the
authoritative CLI registry matches the documented command inventory.

This tool is **read-only**, **non-authoritative**, and **not part of CI**.

### Usage

Direct invocation:

    python scripts/verify_cli_inventory.py

Via Nox helper:

    nox -s verify-cli-inventory

Any mismatch between the CLI registry and the inventory document
is reported as a failure.

---

## CLI Domain Separation Guard

A developer-only mechanical guard is available to enforce the
**Sync vs Delta structural CLI invariant**.

This guard ensures that:
- Sync (execution / transport) and Delta (diagnostic / inspection)
  domains remain strictly separated
- No forbidden command shapes such as `thn sync delta` can exist
- No command module may combine both domains

This tool is **read-only**, **non-authoritative**, and **not part of CI**.

### Usage

Direct invocation:

    python scripts/verify_cli_domain_separation.py

Via Nox helper:

    nox -s verify-cli-domain-separation

Any violation is reported as a failure.

---

## Junk File / Shell Artifact Guard

A developer-only hygiene tool is provided to detect accidental
shell-generated files in the repository.

These files are commonly created by:
- Pasting multi-line text into PowerShell or CMD.exe
- Shell redirection to bare filenames
- Accidental execution of clipboard contents

### Usage

Direct invocation:

    python scripts/forbid_zero_byte_no_ext.py

Strict mode (fail on all artifacts):

    python scripts/forbid_zero_byte_no_ext.py --strict

Machine-readable output:

    python scripts/forbid_zero_byte_no_ext.py --json

### Explanation

    python scripts/forbid_zero_byte_no_ext.py --explain

This prints:

> This check detects junk files accidentally created by shell execution  
> or redirection (commonly caused by pasting text into PowerShell or CMD).  
>  
> Zero-byte, extensionless files are always errors.  
> Known non-zero artifacts (e.g. 'nox') are advisory unless --strict is used.

### Guarantees

- Read-only
- Deterministic
- No deletion performed
- Not user-facing
- Safe for CI and pre-commit

This tool is **developer-only** and does not define runtime behavior.

---

## Diagnostics Output Guarantees

All developer diagnostics emitted by the THN CLI conform to the
Hybrid-Standard diagnostics model.

### Authoritative definitions

- thn_cli/diagnostics/diagnostic_result.py
- thn_cli/diagnostics/suite.py

### Guarantees

- Deterministic structure
- Explicit component attribution
- Read-only semantics
- No mutation or apply inference

This document does not redefine diagnostic schemas.

---

## thn dev cleanup temp

Cleans the THN CLI temporary test root.

This command removes all files and directories under:

    thn_cli/temp_test/

---

### Purpose

- Prevent accumulation of large test artifacts
- Avoid disk exhaustion during Sync apply testing
- Provide a deterministic, safe cleanup mechanism for developers and CI

---

### Behavior

- Deletes all contents under the temp root
- Does NOT delete the temp root itself
- Safe to run repeatedly
- Emits machine-readable JSON to stdout

---

### Example

Command:

    thn dev cleanup temp

Example output:

    {
        "success": true,
        "message": "Temp root cleaned",
        "deleted_paths": [
            "C:\\THN\\core\\cli\\temp_test\\apply_dest"
        ]
    }

If the temp root is already empty:

    {
        "success": true,
        "message": "Temp root cleaned",
        "deleted_paths": []
    }

---

### Notes

- This is a developer utility command
- Output is informational JSON
- Output is not governed by Golden Master contracts
- No --json flag is required
- Future options such as --dry-run may be added later

---

## Status

This document is normative for developer tooling behavior.

It does not define end-user contracts.

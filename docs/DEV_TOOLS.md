# THN CLI Developer Tools

This document describes developer-only utilities provided by the THN CLI.

These commands are intended for:
- Local development
- CI and test environments
- Maintenance and diagnostics

They are not user-facing runtime features.

---

## thn dev cleanup temp

Cleans the THN CLI temporary test root.

This command removes all files and directories under:

    thn_cli/temp_test/

### Purpose

- Prevent accumulation of large test artifacts
- Avoid disk exhaustion during Sync apply testing
- Provide a deterministic, safe cleanup mechanism for developers and CI

### Behavior

- Deletes all contents under the temp root
- Does NOT delete the temp root itself
- Safe to run repeatedly
- Emits machine-readable JSON to stdout

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

### Notes

- This is a developer utility command
- Output is informational JSON
- Output is not governed by Golden Master contracts
- No --json flag is required
- Future options such as --dry-run may be added later

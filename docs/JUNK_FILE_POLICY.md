# THN CLI Junk File Detection Policy

## Status

LOCKED — Advisory / Developer Hygiene

---

## Purpose

This document defines how the THN CLI repository detects and reports
accidental **shell-generated junk files**.

These files are typically created by:
- Accidental pasting of multi-line text into PowerShell or CMD.exe
- Shell redirection to bare identifiers
- Interrupted or malformed shell execution

---

## Artifact Classes

### 1. Zero-byte, extensionless files (FATAL)

Examples:
- `python`
- `Running`
- `Session`

These files indicate broken shell execution and **must be deleted**.

Detection behavior:
- Always reported as ERROR
- Always cause non-zero exit

---

### 2. Known non-zero transient artifacts (ADVISORY)

Examples:
- `nox`

These files:
- Have content
- Have no extension
- Are known to be safe junk artifacts

Detection behavior:
- Reported as NOTICE by default
- May be escalated to ERROR using `--strict`

---

### 3. Legitimate extensionless files (IGNORED)

Examples:
- `Makefile`
- `LICENSE`
- `README`

These files are intentionally excluded and never inferred.

---

## Design Principles

- Explicit allow-listing only
- No inference based on size or name patterns
- No automatic deletion
- No CI enforcement unless explicitly enabled
- Developer visibility over silent cleanup

---

## Strict Mode

The `--strict` flag treats known transient artifacts as errors.

This is intended for:
- Local hygiene checks
- Optional future CI hardening
- Pre-commit enforcement if desired

Strict mode does **not** change zero-byte behavior.

---

## Summary

This policy exists to:
- Catch silent repository pollution early
- Prevent accidental commits of shell junk
- Preserve legitimate extensionless files
- Avoid destructive automation

End of document.

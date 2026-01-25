# THN CLI Developer Tooling Inventory

## Status

DRAFT — Declarative Inventory  
Read-only. No enforcement. No runtime semantics.

---

## Purpose

This document enumerates all **developer-only tooling** provided alongside
the THN CLI source tree.

It exists to:
- Prevent undocumented tooling drift
- Clarify intended scope of internal scripts
- Distinguish developer utilities from release tooling
- Support future audits without introducing enforcement

This document does **not** define behavior or guarantees.

---

## Scope

Included:
- `scripts/` (developer utilities and audits)

Excluded:
- Runtime CLI commands
- CI workflow logic
- Build artifacts

---

## Classification Model

Each tool is classified into **exactly one** category.

### A. Developer Audit / Verification

Read-only tools that:
- Inspect structure, boundaries, or documentation
- Detect drift or invalid shapes
- Never mutate state

### B. Developer Utility

Tools that:
- Assist local development or cleanup
- May mutate local dev-only state
- Are never user-facing

### C. Release / Maintenance Tooling

Tools that:
- Assist packaging, release, or distribution
- Are not part of runtime behavior

---

## Tool Inventory

### scripts/

| Tool | Classification | Purpose | Notes |
|------|----------------|---------|-------|
| `verify_cli_inventory.py` | Audit / Verification | Verify parity between CLI registry and documented inventory | Read-only |
| `verify_cli_domain_separation.py` | Audit / Verification | Detect cross-domain command leakage (sync ↔ delta) | Read-only |
| `verify_diagnostic_domain_purity.py` | Audit / Verification | Ensure diagnostic commands do not import execution engines | Read-only |
| `dev_setup.ps1` | Developer | Windows dev environment setup | Local developer convenience |
| `dev_setup.sh` | Developer | Unix dev environment setup | Local developer convenience |
| `selftest_thn_cli.ps1` | Developer | Windows CLI self-test runner | Non-authoritative |
| `selftest_thn_cli.sh` | Developer | Unix CLI self-test runner | Non-authoritative |
| `selftest_thn_cli.bat` | Developer | Legacy Windows self-test runner | Compatibility |
| `forbid_zero_byte_no_ext.py` | Audit / Verification | Enforce no zero-byte extensionless files | Pre-commit guard (prevent CMD.exe artifacts) |
| `verify_dev_tooling_inventory.py` | Audit / Verification | Verify DEV tooling inventory parity | Developer-only |

(Add rows as needed.)

---

## Invariants

- No tool listed here may be invoked implicitly
- No tool listed here may run in CI unless explicitly documented
- Absence from this inventory constitutes undocumented tooling

---

## Change Policy

Any addition or removal requires:
1. Inventory update
2. Intent-focused changelog entry

Silent additions are prohibited.

---

End of document.

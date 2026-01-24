# THN CLI Release Tooling Inventory

## Status

LOCKED — Declarative Inventory  
Read-only. No runtime behavior. No activation semantics.

---

## Purpose

This document enumerates **release-facing tooling** used to build,
package, document, and publish the THN CLI.

It exists to:

- Declare which scripts participate in release workflows
- Prevent silent introduction of undocumented release tooling
- Provide a stable audit surface for build and publish processes

This document does **not** define behavior or execution order.

---

## Scope

This inventory covers tools located under:

- `tools/`

It explicitly excludes:

- Developer-only utilities
- Verification and audit scripts
- Test helpers

---

## Release Tool Inventory

| Tool | Classification | Purpose |
|------|----------------|---------|
| `build_binary.py` | Release | Build standalone CLI binaries |
| `release_pdf.py` | Release | Generate authoritative PDF documentation |
| `release_pdf_template_c.py` | Release | Locked PDF template |
| `update_changelog.py` | Release | Normalize and prepare changelog |
| `generate_api_docs.py` | Release | Generate API documentation |
| `generate_policy_pdf.py` | Release | Build policy documentation |
| `generate_tenant_docs.py` | Release | Tenant documentation generator |
| `extract_version.py` | Release | Extract version metadata |
| `thn_release_tui.py` | Release | Interactive release UI |
| `syncv2_negotiation_viz.py` | Visualization | Sync negotiation visualization |
| `delta_inspector_report.py` | Visualization | CDC inspection reporting |

(Add rows as needed.)

---

## Invariants

- Every release tool must be listed exactly once
- No undocumented release tooling may exist
- Inventory presence does **not** imply execution authority
- Inventory does **not** define CI or workflow usage

---

## Change Policy

Any change requires:

1. Tool addition / removal
2. Inventory update
3. Changelog entry (intent only)

Silent changes are prohibited.

---

## Summary

This document freezes the **release tooling surface**.

It answers:
- What release tools exist
- Why they exist (at a high level)

Nothing more.

End of document.

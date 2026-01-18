# Documentation Templates

This directory contains **Jinja2-based documentation templates**
used throughout the THN documentation system.

Templates provide structure and consistency for:

- Tenant documentation
- Project and module generators
- Sync V2 reports
- Blueprint documentation
- Automated exports

---

## Usage

Templates are rendered by internal tooling.

Example:

`python tools/generate_tenant_docs.py --input tenants.json --out docs/tenants/`

---

## Standards

All templates:

- Follow THN formatting and naming conventions
- Avoid embedding behavior or policy
- Are presentation-only

Templates must not:

- Encode execution semantics
- Imply authority
- Introduce policy decisions

---

## Change Policy

Templates may evolve structurally, but must remain compatible with
existing tooling unless versioned explicitly.

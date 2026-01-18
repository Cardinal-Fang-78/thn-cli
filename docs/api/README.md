# THN CLI API Documentation

This directory contains **auto-generated API documentation** for the THN CLI.

The files in this directory are produced by internal tooling and are
**derived from source code**, not authored manually.

---

## Scope

Generated API documentation covers:

- Core CLI modules
- Sync V2 engine and helpers
- Routing and targeting logic
- Diagnostics emitters and structures
- Task and plugin interfaces
- UI-facing abstractions (where applicable)

---

## Generation

API documentation is generated using:

`python tools/generate_api_docs.py`

The script emits `.md` files that map directly to module-level
responsibilities and public interfaces.

---

## Authority and Guarantees

- API docs are **descriptive**, not normative
- They do **not** define contracts or invariants
- They must not be used to infer behavior guarantees

Authoritative contracts live under:

- `docs/diagnostics/`
- `docs/history/`
- `docs/recovery/`
- `docs/syncv2/`

---

## Change Policy

Manual edits to generated files are discouraged.

Any behavioral guarantees must be documented in the appropriate
contract or invariants ledger, not here.

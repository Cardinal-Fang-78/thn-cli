# PDF Exports

This directory contains **generated PDF versions** of selected THN
documentation.

PDFs are intended for:

- Offline reading
- Archival snapshots
- Distribution outside the repository

---

## Contents

PDF exports may include:

- THN Versioning Policy
- Diagnostics and contract documentation
- Sync V2 reports and mutation plans
- Release notes
- Negotiation and visualization outputs

---

## Generation

PDFs are generated using the THN documentation pipeline:

`python tools/generate_policy_pdf.py`
`python tools/release_pdf.py`

---

## Formatting Standards

All PDFs:

- Use THN-standard dark backgrounds (`#444444`)
- Use light text for readability
- Mirror the authoritative Markdown source

---

## Authority

PDFs are **rendered artifacts only**.

They do not introduce new guarantees and must always be considered
secondary to the Markdown source files under `/docs`.

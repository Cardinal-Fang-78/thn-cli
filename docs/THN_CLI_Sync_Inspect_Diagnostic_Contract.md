# THN CLI – Sync Inspect Diagnostic Contract

## Status
LOCKED — DIAGNOSTIC SURFACE

---

## Purpose

`thn sync inspect` provides a **diagnostic and observational view** of a Sync V2 envelope.

It exists to:
- Aid human inspection
- Surface structural summaries
- Expose diagnostic findings for debugging and validation

It is **not** an execution, enforcement, or decision-making surface.

---

## Authoritative Boundary

`inspect` is **non-authoritative**.

It MUST NOT be interpreted as defining:
- Execution success or failure
- Envelope acceptability
- Policy compliance
- Apply readiness
- Health or correctness guarantees

All authoritative behavior belongs to:
- The Sync V2 engine
- Explicit validation paths
- Apply-time execution results

---

## Output Semantics

Inspect output intentionally blends:

- **Structural information**
  - Manifest content
  - File summaries
  - Envelope metadata

- **Diagnostic findings**
  - Payload completeness checks
  - Validation errors or warnings
  - Observational signals

These signals are **descriptive**, not normative.

---

## Decision Safety Rules

Inspect output MUST NOT be used for:
- Automation branching
- Policy enforcement
- Apply gating
- Health assertions
- CI pass/fail signals

Any such usage is explicitly unsupported.

---

## Screenshot Safety

Inspect output is considered **diagnostic-only**.

It is safe to:
- Screenshot for debugging
- Share for analysis
- Use in documentation examples

It is unsafe to:
- Present as proof of correctness
- Use as an execution outcome
- Treat as authoritative evidence

---

## Forward Compatibility

Inspect output is labeled as diagnostic to preserve future evolution.

Future versions MAY:
- Split structural and diagnostic views
- Introduce presentation-only filtering
- Add scoped inspection modes

Such changes will clarify intent, not alter semantics.

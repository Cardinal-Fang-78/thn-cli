# THN CLI Diagnostics Normalization Contract

---

## 1. Purpose

This document defines the **normalization contract** for THN CLI diagnostics.

Normalization is a **presentation-layer operation** applied to diagnostic output
to improve readability, consistency, and tooling interoperability.

Normalization is **non-authoritative**.

It exists to ensure that diagnostic output can be safely consumed, compared,
stored, and re-serialized **without introducing enforcement, policy, or
behavioral coupling**.

---

## 2. Scope

This contract applies to:

- All diagnostic-emitting commands (e.g. `thn diag *`)
- Any normalized diagnostic payload produced by the CLI
- All consumers of normalized diagnostic output

This contract does **not** apply to:

- Authoritative engine outputs
- Error contracts or exit code behavior
- Mutation, apply, or repair workflows
- Strict validation or enforcement layers

---

## 3. Definition of Normalization

**Normalization** is a presentation-only transformation that may:

- Reorder fields for readability
- Group related diagnostic entries
- Apply consistent key naming
- Aggregate multiple diagnostic suites into a single payload

Normalization **must never**:

- Add semantic meaning
- Remove unknown fields
- Infer severity or health
- Alter runtime behavior
- Affect command availability or exit codes

Normalization is **lossy-safe** and **semantically inert**.

---

## 4. Consumer Guarantees

Consumers of normalized diagnostic output may rely on the following guarantees.

### 4.1 Structural Guarantees

When normalized diagnostics are emitted in structured form (e.g. JSON):

- The payload is valid JSON
- Field ordering is non-semantic
- Field presence is additive, not exhaustive
- Unknown fields may appear at any level

Consumers must tolerate schema expansion.

---

### 4.2 Unknown Field Preservation

Normalization **must not drop**:

- Unknown top-level fields
- Unknown diagnostic-entry fields
- Unknown nested metadata

Consumers may safely:

- Deserialize and re-serialize normalized output
- Store normalized payloads for later inspection
- Forward normalized output across tooling boundaries

---

### 4.3 Non-Enforcement Guarantee

Normalization does **not**:

- Block unrelated commands
- Alter exit codes
- Gate CLI behavior
- Imply success or failure
- Participate in policy decisions

All enforcement semantics remain governed by:

- Engine behavior
- Error contracts
- Explicit policy layers

---

## 5. Relationship to Diagnostic Metadata

Diagnostic metadata (including but not limited to):

- `category`
- `severity`
- `source`
- `notes`

is **descriptive only**.

Normalization may standardize metadata presentation but must not:

- Reinterpret metadata
- Promote metadata to enforcement signals
- Require consumers to branch on metadata values

---

## 6. Relationship to Errors

Errors are governed exclusively by:

- `ERROR_CONTRACTS.md`
- Code-level error contracts

Normalization **does not**:

- Downgrade errors
- Escalate diagnostics to errors
- Alter error rendering or exit behavior

Diagnostics remain observational even when errors are present.

---

## 7. Compatibility Model

Diagnostics normalization operates under a **non-strict compatibility model**:

- Missing fields are tolerated
- Extra fields are tolerated
- Field ordering is irrelevant
- Schema evolution is additive

No downgrade or compatibility enforcement occurs at runtime.

---

## 8. Explicit Non-Goals

This contract does **not** define:

- Severity semantics
- Health scoring
- CI enforcement
- Strict schema validation
- Version pinning requirements

Such behavior must be introduced as **explicit, opt-in policy layers**
and must not weaken the guarantees in this document.

---

## 9. Test-Backed Guarantees

The guarantees in this document are enforced by **contract tests** that ensure:

- Normalization does not drop unknown fields
- Normalization does not enforce behavior
- Normalization does not affect unrelated commands
- Normalized output is safely re-serializable

These tests exist to prevent accidental semantic drift.

---

## Contract Status

**LOCKED — Normalization Contract**

Any change requires:

- Documentation updates
- Corresponding contract test updates
- Explicit versioning if guarantees are altered

---

## Related Documents

- `diagnostics_consumer_contracts.md`
- `THN_CLI_Contract_Boundaries.md`
- `ERROR_CONTRACTS.md`
- `THN_CLI_Sync_History_Diagnostics.md`
- `THN_Versioning_Policy.md`

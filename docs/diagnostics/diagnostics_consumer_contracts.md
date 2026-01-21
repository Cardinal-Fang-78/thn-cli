# THN CLI Diagnostics Consumer Contracts

---

## 1. Purpose

This document defines the **consumer-facing contracts** for THN CLI diagnostics.

Diagnostics are **observational telemetry only**. They describe system state at a
point in time, but **never enforce policy**, **never alter runtime behavior**, and
**never affect command availability or exit semantics**.

This contract exists to ensure that:

- Diagnostic producers can evolve safely
- Diagnostic consumers remain robust to change
- CLI behavior remains deterministic and policy-driven elsewhere
- No accidental coupling or enforcement emerges through diagnostics

This document is **non-authoritative** with respect to runtime behavior.

---

## 2. Scope

This contract applies to:

- All `thn diag *` commands
- Any consumer parsing, storing, forwarding, or visualizing diagnostic output
- Internal and external tooling (CLI wrappers, GUIs, CI systems)

This contract does **not** apply to:

- Non-diagnostic commands
- Authoritative command outputs
- Mutation, apply, or repair workflows
- Policy or enforcement layers

---

## 3. Consumer Guarantees (What Is Safe to Assume)

Consumers of THN CLI diagnostics may rely on the following guarantees.

### 3.1 Structural Guarantees

When a diagnostic command emits structured output (for example JSON):

- The payload is valid JSON
- Top-level fields **may include**, but are not limited to:
  - `ok`
  - `diagnostics`
  - `errors`
  - `warnings`

Field presence is **not exhaustive** and **not exclusive**.

Consumers must tolerate additional fields and must not assume a closed schema.

---

### 3.2 Behavioral Guarantees

Executing diagnostics:

- Does **not** mutate global CLI state
- Does **not** alter configuration, registry, or environment
- Does **not** affect command availability
- Does **not** affect exit codes of unrelated commands
- Does **not** change runtime behavior

Diagnostics are **non-authoritative by design**.

CLI command authority boundaries are formally declared in
`THN_CLI_Command_Authority_Boundaries.md`; diagnostics must never be treated
as execution or policy signals by any command.

---

### 3.3 Topology and Command Isolation

Consumers **must not assume**:

- A stable subcommand hierarchy
- The continued existence of any specific diagnostic subcommand
- That unrelated commands are safe probes for enforcement

Contract tests intentionally use **top-level help or version commands**
to avoid coupling these guarantees to a specific command topology.

---

### 3.4 Forward-Compatibility Guarantees

Consumers must tolerate:

- Unknown top-level fields
- Unknown diagnostic-entry fields
- Unknown nested metadata objects

Unknown fields are **additive only** and must be ignored safely.

Consumers must avoid strict schema validation that would fail on expansion.

---

## 4. Non-Guarantees (What Consumers Must Not Assume)

Consumers **must not** assume any of the following:

- That diagnostic categories imply severity
- That errors imply failure
- That warnings imply degraded behavior
- That error counts map to health
- That diagnostics influence policy decisions
- That diagnostic schemas are complete
- That diagnostic ordering is stable
- That diagnostic output implies mutation or repair

Diagnostics are **descriptive snapshots**, not enforcement signals.

---

## 5. Diagnostic Metadata Semantics

Diagnostic metadata fields are **descriptive only**.

This includes (but is not limited to):

- `category`
- `severity`
- `source`
- `notes`
- Any future metadata fields not explicitly documented as authoritative

Metadata is:

- Non-semantic
- Non-enforcing
- Non-filtering

Consumers **must not** branch behavior or enforce policy based on metadata.

Normalization performed during DX-1.6 was a **presentation consistency measure**,
not a behavioral contract.

---

## 6. Aggregated Errors

Diagnostic payloads may include aggregated errors.

These errors:

- Do **not** imply CLI invalidity
- Do **not** block subsequent commands
- Do **not** alter command parsing or availability

Aggregated errors are **reporting artifacts**, not enforcement signals.

---

## 7. JSON Flags and Compatibility Stubs

Some diagnostic flags (for example `--json`) exist for **legacy or compatibility
purposes**.

Current guarantees:

- Compatibility flags do **not** alter diagnostic semantics
- Presence or absence of such flags must not change meaning
- Consumers must not branch behavior based on these flags

Compatibility flags may be removed in the future.

When removed:

- Associated golden or contract tests will be deleted
- No semantic behavior change will occur

---

## 8. Downgrade and Compatibility Model (Non-Strict)

Diagnostics operate under a **non-strict compatibility model** by default.

This means:

- Missing fields are tolerated
- Extra fields are tolerated
- Field ordering is non-semantic
- Schema expansion is additive

Consumers should:

- Prefer presence checks over strict validation
- Treat missing optional fields as “unknown,” not erroneous

No downgrade or enforcement occurs at runtime.

---

## 9. Test-Backed Contracts (Traceability)

The following guarantees are enforced via **contract-level tests** under
`tests/contract/`:

- Diagnostic isolation from unrelated commands
- Non-enforcement of aggregated errors
- Tolerance of unknown fields
- Non-semantic handling of diagnostic metadata
- Topology-agnostic command probing

These tests exist to prevent accidental coupling or inference.

---

## 10. Out of Scope (Explicitly Deferred)

This document does **not** define:

- Severity policies
- Error downgrade or escalation rules
- Health scoring or automation
- UI interpretation rules
- Strict validation or enforcement

Such changes are **policy decisions** and belong in future DX branches.

---

## 11. Future Extension: Strict Mode (Deferred)

A future **diagnostic strict mode** may introduce:

- Schema validation
- Severity enforcement
- Version pinning
- CI-oriented failure signaling

Strict mode is **explicitly opt-in** and not enabled by default.

No current diagnostic behavior implies or anticipates strict-mode semantics.

---

## Contract Status

**LOCKED — Consumer Contracts**

Any change to these guarantees requires:

- Explicit versioning
- Updated documentation
- Corresponding contract test changes

---

## Relationship to Contract Boundaries

This document governs **how diagnostic output may be consumed**.

It is complementary to, but distinct from:

- **THN_CLI_Contract_Boundaries.md**

That document defines **command and field authority**
(authoritative vs diagnostic vs presentation).

This document defines **consumer behavior guarantees** for diagnostics.

Together, they establish a two-axis model:

- **Authority** — what the CLI and engine own
- **Consumption** — how diagnostic output may be interpreted

No diagnostic consumer behavior may contradict the guarantees defined here.

---

## Related Contracts and References

### Core Diagnostic Contracts

- **THN_CLI_Sync_History_Diagnostics.md**
- **THN_CLI_Sync_History_Diagnostic_Contract.md**
- **THN_CLI_Sync_Inspect_Diagnostic_Contract.md**
- **THN_CLI_Sync_Status_Diagnostic_Contract.md**

### Boundary and Policy Context

- **THN_CLI_Contract_Boundaries.md**
- **ERROR_CONTRACTS.md**
- **THN_CLI_First_Time_Output_Policy.md**

### GUI and Unified History Consumers

- **THN_GUI_History_Contracts_Index.md**
- **THN_Sync_Unified_History_Reader.md**

### Explicit Exclusions

- **THN_Sync_Unified_History_Strict_Mode.md** (future policy layer)
- **THN_Versioning_Policy.md** (schema evolution only)

Any future downgrade, enforcement, or strict-mode behavior must be introduced
as an **additive layer** that does not reinterpret or weaken the guarantees in
this document.

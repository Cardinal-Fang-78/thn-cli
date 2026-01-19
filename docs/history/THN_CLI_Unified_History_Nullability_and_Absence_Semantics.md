# THN CLI Unified History Nullability and Absence Semantics

LOCKED — Design-Only Semantics Declaration  
Read-only. Declarative. No runtime effect.

This document defines **nullability, absence, and omission semantics**
for all Unified History fields and aggregates. It does **not** introduce
validation, enforcement, inference, replay, recovery, or mutation behavior.

Verified against repository state at commit:
`ab9e86792ede9e3071c4cdd19d923e2cefc6bd56`

---

## Purpose

This document exists to:

- Define **what it means when Unified History data is absent**
- Eliminate ambiguity between `null`, empty, and omitted fields
- Prevent inference from missing or partial observability
- Provide stable interpretation rules for CLI and GUI consumers
- Lock semantics without enforcing behavior

This document governs **interpretation only**, not execution.

---

## Core Principle

> **Absence is informative, but never actionable.**

Missing Unified History data must be:
- Preserved
- Rendered honestly
- Never inferred against
- Never treated as failure, success, or intent

Absence is **not an error**.  
Absence is **not a signal**.  
Absence is **not a trigger**.

---

## Definitions

**Absent**  
A field or record is not present at all.

**Null**  
A field is present but explicitly set to `null`.

**Empty**  
A field is present with an empty value (e.g., empty array or object).

**Partial**  
A record exists, but required complementary records do not.

---

## Global Interpretation Rules

The following rules apply to **all Unified History data**:

1. Absence MUST NOT be inferred as failure or success
2. Absence MUST NOT trigger recovery, replay, or diagnostics escalation
3. Absence MUST be preserved through all read surfaces
4. Absence MUST NOT be synthesized or backfilled
5. Absence MUST NOT be reinterpreted across sources

No component may "fix", "complete", or "normalize" missing history.

---

## Field-Level Nullability Semantics

### Field: `history`

| Condition | Meaning | Prohibited Interpretation |
|--------|--------|---------------------------|
| Absent | Unified History not available | Failure, misconfiguration |
| Null | Explicitly unavailable | No semantic implication |
| Empty | No history recorded | No executions occurred |

Notes:
- `history` absence must be rendered verbatim
- No implicit aggregation is permitted

---

### Field: `status`

| Condition | Meaning | Prohibited Interpretation |
|--------|--------|---------------------------|
| Absent | No successful execution recorded | Failure |
| Null | Explicitly unavailable | No inference permitted |
| Empty | No qualifying records | Not an error |

Notes:
- Status DB absence is intentional for failures
- Missing status is **not exceptional**

---

### Field: `txlog`

| Condition | Meaning | Prohibited Interpretation |
|--------|--------|---------------------------|
| Absent | No diagnostic trace | Clean execution |
| Null | Logging unavailable | Success |
| Empty | No recorded diagnostic events | No-op execution |

Notes:
- TXLOG is best-effort
- Absence carries no semantic weight

---

### Field: `entries`

| Condition | Meaning | Prohibited Interpretation |
|--------|--------|---------------------------|
| Absent | No visible executions | Failure |
| Null | Entries intentionally withheld | Error |
| Empty | No recorded executions | No action implied |

---

### Field: `strict`

| Condition | Meaning | Prohibited Interpretation |
|--------|--------|---------------------------|
| Absent | Strict mode inactive | Relaxed enforcement |
| Null | Strict context unknown | Error |
| Present | Strict metadata declared | Enforcement enabled |

Notes:
- Strict mode is inert by default
- Presence does not imply behavior

---

## Cross-Source Absence Semantics

The following combinations are **explicitly valid**:

| Status DB | TXLOG | Meaning |
|--------|------|--------|
| Present | Absent | Successful execution without diagnostics |
| Absent | Present | Diagnostic trace without terminal success |
| Absent | Absent | No observable history |

None of these combinations imply error, failure, or inconsistency.

---

## CLI Presentation Rules

CLI consumers MUST:

- Render missing fields explicitly
- Avoid placeholder synthesis
- Avoid wording implying failure or error
- Avoid suggesting remediation

CLI output is **descriptive only**.

---

## GUI Presentation Rules

GUI consumers MUST:

- Preserve absence as absence
- Avoid inferred timelines
- Avoid action suggestions based on missing data
- Avoid visual severity escalation

GUI presentation is **non-operational**.

---

## Prohibited Behaviors

The following are explicitly forbidden:

- Inferring intent from missing records
- Backfilling absent fields
- Ordering executions based on partial data
- Treating absence as an error condition
- Generating synthetic placeholders
- Escalating diagnostics due to absence

Any occurrence is a defect.

---

## Governance

This document is subordinate to:

- `THN_CLI_Unified_History_Invariants_Ledger.md`
- `THN_CLI_Unified_History_Field_Contracts_v1.md`
- `THN_CLI_Unified_History_Schema_v1.md`
- `THN_Unified_History_Evolution_and_Change_Policy.md`

In case of conflict:
**Invariants → Field Contracts → Schema → Nullability Semantics**

---

## Change Policy

Any change to nullability or absence interpretation requires:

1. Explicit documentation update
2. Cross-review against invariants and field contracts
3. Change classification under the evolution policy

Silent reinterpretation is prohibited.

---

## Summary

Unified History absence semantics are:

- Explicit
- Non-inferential
- Non-actionable
- Preserved end-to-end

Missing data remains missing — by design.

This document ensures Unified History consumers cannot accidentally
convert observability gaps into behavior, inference, or control.

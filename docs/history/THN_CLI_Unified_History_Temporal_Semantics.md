# THN CLI Unified History
Temporal Semantics

LOCKED — Design-Only Semantics Declaration  
Read-only. Declarative. No runtime effect.

This document defines **temporal interpretation semantics** for all
Unified History data. It governs how timestamps, ordering, and sequence
information may be **interpreted**, and explicitly forbids their use for
execution control, inference, replay, recovery, or mutation.

Verified against repository state at commit:
`aa320fd39b4a27bff726741ead781a00404d86c0`

---

## Purpose

This document exists to:

- Define what Unified History timestamps and ordering **mean**
- Prevent inference of causality, progression, or execution outcome from time data
- Eliminate ambiguity around “latest”, “earliest”, and ordering semantics
- Lock time-related interpretation rules for CLI and GUI consumers
- Ensure temporal data remains descriptive and non-operational

This document governs **interpretation only**, not execution.

---

## Core Principle

> **Time describes observations, not causality.**

Temporal data in Unified History:
- Describes *when something was observed or recorded*
- Does **not** describe why it occurred
- Does **not** imply order-dependent correctness or outcome
- Must never influence behavior
- Temporal ordering may exist in non-history subsystems (snapshots, drift history, diagnostics
  presentation) as a deterministic presentation or selection aid, but Unified History must **not** infer semantics from ordering across sources.

Time is **metadata**, not control flow.

---

## Definitions

**Timestamp**  
A recorded point in time associated with an event, record, or observation.

**Ordering**  
The relative sequence in which records are presented or stored.

**Temporal Gap**  
A missing or discontinuous span of time with no recorded history.

**Out-of-Order Record**  
A record whose timestamp or presentation order does not align with
other records.

---

## Global Temporal Interpretation Rules

The following rules apply to **all Unified History temporal data**:

1. Timestamps MUST be treated as descriptive metadata only
2. Ordering MUST NOT imply causality, success, failure, or intent
3. Temporal gaps MUST NOT be interpreted as errors or anomalies
4. Out-of-order records MUST be preserved as-is
5. No component may infer execution flow from time data

Temporal data MUST NOT:
- Drive execution
- Trigger recovery or replay
- Escalate diagnostics
- Influence strict-mode behavior
- Affect policy decisions

---

## Timestamp Semantics

### Meaning of Timestamps

A timestamp indicates **when a record was written or observed**, not when
an action *logically* occurred.

Timestamps MAY represent:
- Write time
- Observation time
- Best-effort logging time

Timestamps do NOT represent:
- Causal order
- Execution dependency
- Transaction boundaries
- Success or failure signals

---

### Missing or Invalid Timestamps

| Condition | Meaning | Prohibited Interpretation |
|--------|--------|---------------------------|
| Absent | Time not recorded | Failure or corruption |
| Null | Explicitly unavailable | Error or retry required |
| Invalid | Unparseable or malformed | Inference or correction |

Missing or invalid timestamps MUST be preserved verbatim.

---

## Ordering Semantics

### Record Ordering

The order in which Unified History records appear:

- Is **presentation-only**
- May reflect filesystem, storage, or aggregation order
- Must not be treated as authoritative execution order

Ordering MUST NOT be used to:
- Infer which operation happened “first” or “last”
- Resolve conflicts
- Deduce partial or complete execution
- Infer rollback, replay, or retry behavior

---

### “Latest” and “Earliest” Concepts

Terms such as “latest”, “earliest”, or “most recent”:

- Are **presentation conveniences only**
- Do not imply correctness or finality
- Must never suppress or override other records

Any UI or CLI use of such terms is **non-authoritative**.

---

## Cross-Source Temporal Semantics

When multiple sources provide time data (e.g., Status DB, TXLOG):

- Disagreement is acceptable
- Absence in one source does not invalidate another
- No reconciliation or normalization is permitted

The system MUST NOT:
- Synthesize unified timelines
- Reorder records to “make sense”
- Repair temporal inconsistencies

---

## CLI Presentation Rules

CLI consumers MUST:

- Render timestamps verbatim
- Preserve ordering as received
- Avoid language implying causality or progression
- Avoid “latest implies success” phrasing

CLI output is **descriptive only**.

---

## GUI Presentation Rules

GUI consumers MUST:

- Treat time as informational metadata
- Avoid timeline inference or animations implying progression
- Avoid visual severity escalation based on recency
- Avoid collapsing or hiding records based on timestamps

GUI presentation is **non-operational**.

---

## Prohibited Behaviors

The following behaviors are explicitly forbidden:

- Inferring execution order from timestamps
- Treating “newer” records as more correct
- Suppressing records due to age
- Reconstructing timelines to imply causality
- Triggering recovery, replay, or mutation based on time
- Using timestamps to drive strict-mode enforcement

Any occurrence is a defect.

---

## Governance

This document is subordinate to:

- `THN_CLI_Unified_History_Invariants_Ledger.md`
- `THN_CLI_Unified_History_Field_Contracts_v1.md`
- `THN_CLI_Unified_History_Schema_v1.md`
- `THN_CLI_Unified_History_Nullability_and_Absence_Semantics.md`
- `THN_Unified_History_Evolution_and_Change_Policy.md`

In case of conflict:
**Invariants → Field Contracts → Schema → Nullability → Temporal Semantics**

---

## Change Policy

Any change to temporal interpretation requires:

1. Explicit documentation update
2. Cross-review against invariants and schema
3. Classification under the evolution policy

Silent reinterpretation is prohibited.

---

## Summary

Unified History temporal semantics are:

- Descriptive
- Non-causal
- Non-operational
- Preserved end-to-end

Time data may explain *when* something was observed,  
but never *what it means* or *what should happen next*.

This document ensures Unified History cannot accidentally
turn timestamps into control flow.

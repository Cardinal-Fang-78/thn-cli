# THN CLI Command Authority Boundaries

## Status

LOCKED — Declarative Authority Contract  
Read-only. No runtime effect. No activation semantics.

---

## Verification Note

This document was verified against the authoritative CLI command registry
and boundary classification code as of commit:

`e12533677df845bfb53478e2171affa826b83d17`

Verification included:

- Exhaustive comparison against `thn_cli.commands.__all__`
- Validation of top-level command coverage
- Cross-check of all explicit path-level overrides in
  `thn_cli/contracts/cli_boundaries.py`
- Confirmation that no CLI command lacks an explicit authority classification
- Confirmation that no undocumented CLI surfaces exist

All commands listed here:
- Are explicitly registered in the CLI
- Have a deterministic authority classification
- Are governed by the Hybrid-Standard CLI boundary registry

Any future command added to the CLI without a corresponding update to this
document and the boundary registry constitutes a defect.

---


## Purpose

This document defines the **authoritative boundaries of all THN CLI commands**.

It exists to:

- Prevent accidental escalation of CLI authority
- Explicitly classify which commands may mutate state
- Lock read-only and diagnostic-only commands as non-authoritative
- Prevent history-, diagnostic-, or strict-mode–driven execution
- Provide a stable reference for future command additions

This document does **not** define command behavior.  
It declares **what commands are allowed to do** and, critically, **what they must never do**.

---

## Authority Model

All THN CLI commands fall into **exactly one** of the following authority classes.

### 1. Execution Authority

Commands that:
- Mutate filesystem or project state
- Apply migrations, syncs, or recovery actions
- Execute engine-controlled behavior

Execution authority is **explicit**, **opt-in**, and **command-scoped**.

Execution-authoritative commands must never:
- Read Unified History to make decisions
- Read diagnostics to infer correctness
- Escalate policy based on historical absence or presence

---

### 2. Presentation Authority (Read-Only)

Commands that:
- Read existing data
- Aggregate or format results
- Emit JSON or human-readable output only

Presentation authority is:
- Read-only
- Non-inferential
- Non-operational

Presentation commands must never:
- Mutate state
- Trigger execution
- Activate recovery
- Enforce policy

---

### 3. Diagnostic Authority (Observational Only)

Commands that:
- Inspect state
- Emit warnings or annotations
- Classify or normalize diagnostic output

Diagnostic authority is:
- Non-blocking
- Non-enforcing
- Explicitly non-authoritative

Diagnostics may **describe**, but must never **decide**.

---

## Cross-Domain Authority Invariants

The following invariants apply globally to the THN CLI and constrain
all current and future command shapes.

### Domain Separation Invariant

- Diagnostic domains (e.g., `delta`, `inspect`, `diag`) MUST remain
  top-level and MUST NOT be nested under execution domains.
- Execution-capable commands MUST be reachable only through explicitly
  execution-authoritative roots (e.g., `sync`, `recover`, `migrate`).
- No command name may imply execution adjacency unless execution authority
  is explicitly granted.

### Naming Invariant

- Top-level command names reflect **authority class**, not implementation detail.
- Commands that inspect, classify, or analyze state MUST NOT be named
  as subcommands of execution domains.
- Shapes such as `thn sync delta` are explicitly forbidden.

Violation of these invariants constitutes a CLI authority defect.

---

## Command Classification

### A. Execution-Authoritative Commands

These commands are the **only CLI surfaces permitted to mutate state**.

| Command | Authority | Notes |
|------|---------|------|
| `thn sync apply` | Execution | Engine-owned mutation |
| `thn sync delta apply` | Execution | CDC mutation |
| `thn migrate apply` | Execution | Versioned migration |
| `thn make` | Execution | Scaffold creation |
| `thn accept` | Execution | Policy-gated mutation |
| `thn routing apply` | Execution | Routing mutation |
| `thn registry *` (mutating) | Execution | Registry writes |
| `thn recovery apply` | Execution | Explicit, policy-gated |

**Invariants**
- Execution commands must never consult Unified History
- Diagnostics must not alter execution outcome
- Strict mode must not escalate authority

---

### B. Read-Only History Presentation Commands

These commands expose **history or lineage data only**.

| Command | Authority | Notes |
|------|---------|------|
| `thn sync history` | Presentation | JSON-only |
| `thn drift history` | Presentation | Diagnostic timeline |
| `thn snapshots diff` | Presentation | Structural comparison |
| `thn snapshots inspect` | Presentation | Read-only |
| `thn sync status` | Presentation | Alias, JSON-enforced |
| GUI history API | Presentation | Read-only contract |

**Invariants**
- No inference
- No repair
- No reconciliation
- No execution authority

---

### C. Diagnostic-Only Commands

These commands are **observational probes only**.

| Command | Authority | Notes |
|------|---------|------|
| `thn inspect *` | Diagnostic | Read-only |
| `thn diag *` | Diagnostic | Normalized output |
| `thn drift preview` | Diagnostic | No enforcement |
| `thn drift explain` | Diagnostic | No mutation |
| `thn recover inspect` | Diagnostic | Non-blocking |
| Snapshot lineage tools | Diagnostic | Annotative only |

**Invariants**
- Diagnostics must never block execution
- Diagnostics must never trigger recovery
- Diagnostics must never escalate policy

---

## Relationship to the CLI Command Inventory

The authoritative enumeration of all CLI commands governed by this document
is maintained in:

- `docs/cli/THN_CLI_Command_Inventory.md`

That inventory:
- Enumerates every CLI command exposed via `thn_cli.commands.__all__`
- Records the declared authority class for each command
- Mirrors the authoritative boundary registry in code
- Does **not** define behavior, semantics, flags, or output contracts

This document defines **authority rules**.  
The inventory verifies **surface coverage**.

Neither document may be used to infer runtime behavior.

---

## Strict Mode Semantics

Strict mode within the THN CLI is:

- Explicitly opt-in
- Diagnostic-only
- Non-blocking
- Non-enforcing

Strict mode may:
- Add warnings
- Add metadata
- Increase diagnostic verbosity

Strict mode must never:
- Change exit codes
- Block execution
- Trigger recovery
- Enforce policy
- Escalate authority

---

## Explicitly Forbidden Authority

The following **must not exist**:

- History-driven execution
- Diagnostic-driven recovery
- Replay or reconstruction commands
- Implicit repair or reconciliation
- Policy escalation based on absence of records
- Strict-mode enforcement

Any appearance of the above constitutes a defect.

---

### Forbidden Command Shapes

The following command shapes must never exist:

- `thn sync delta`
- `thn sync inspect-delta`
- Any delta-prefixed command under execution domains

Rationale:
- Delta is a diagnostic domain, not an execution phase
- Sync execution must not be semantically gated by inspection tools

---

## Structural CLI Invariants

### Why `thn cli` Does Not Exist

LOCKED — Structural CLI Design Invariant  
Normative. Governance-only. No runtime semantics.

---

### Purpose

This policy explains **why the THN CLI intentionally does not expose a top-level
`thn cli` command**, despite the presence of CLI-related tooling, assets,
and diagnostics.

It exists to:

- Prevent namespace confusion
- Enforce architectural separation
- Preserve long-term CLI stability
- Eliminate ambiguous authority surfaces

---

### Core Principle

**The CLI is the control plane, not a managed subsystem.**

A command named `thn cli` would imply that:
- The CLI can manage itself as a first-class runtime target
- CLI state is mutable via the CLI
- CLI internals are a governed execution domain

All of these implications are **false by design**.

---

### Architectural Rationale

#### 1. The CLI is not a domain

THN domains are **things the CLI operates on**, such as:

- Projects
- Scaffolds
- Sync envelopes
- Registries
- Snapshots
- CDC delta artifacts

The CLI itself is **not** one of these.

Introducing `thn cli` would create a circular control relationship
that violates Hybrid-Standard authority boundaries.

---

#### 2. CLI assets already have an explicit owner

Operations that affect CLI assets are intentionally routed through
existing, correctly scoped domains:

- `thn sync cli` — distribution of CLI artifacts (transport concern)
- `thn dev *` — developer utilities (diagnostic concern)
- Build and release tooling — external to the CLI runtime

This ensures:
- No new authority class is introduced
- No self-mutation surface exists
- No special-case exception is required

---

#### 3. Preventing authority ambiguity

A `thn cli` command would be ambiguous by default:

- Is it execution-authoritative?
- Is it diagnostic?
- Is it presentation-only?
- Can it mutate the CLI installation?
- Can it trigger recovery or updates?

Because no safe default exists, the command is **disallowed entirely**.

This aligns with the THN Tenet:

> When no structurally correct default exists, the feature must not exist.

---

#### 4. Namespace hygiene and user clarity

User-facing commands must describe **what they operate on**, not how.

Examples:
- `thn sync` → synchronization
- `thn delta` → CDC-delta artifacts
- `thn registry` → registry state
- `thn routing` → routing configuration

`thn cli` would describe the interface itself, not a domain.
This violates the CLI naming model and is therefore prohibited.

---

### Locked Invariant

The following invariant is **final and enforced**:

**No top-level `thn cli` command may exist.**

Consequences:

- CLI-related functionality must live under an appropriate domain
- CLI distribution is handled via `sync`
- CLI diagnostics are handled via `dev` or `diag`
- CLI metadata may be presented, but never managed, by the CLI itself

Any attempt to introduce `thn cli` constitutes a **design defect**, not a
missing feature.

---

### Relationship to Other Governance Documents

This policy is consistent with and constrained by:

- THN_CLI_Command_Inventory.md
- THN_CLI_Command_Authority_Boundaries.md
- THN_CLI_DX2_Invariants.md
- Hybrid-Standard authority rules

It introduces **no new authority**, **no new commands**, and **no new semantics**.

---

### Change Policy

This invariant may only be changed if **all** of the following occur:

1. A new authority class is formally defined
2. CLI self-management semantics are explicitly designed
3. All governance documents are updated
4. A migration path is documented
5. Golden tests and boundary validators are updated

Absent these conditions, the invariant is final.

---

### Summary

- The CLI is the control plane, not a managed domain
- Self-management commands are structurally unsafe
- Existing domains already cover all legitimate use cases
- `thn cli` is intentionally forbidden

This is not an omission.  
It is a design guarantee.

End of policy.

---

## Relationship to Other Governance Documents

This document is constrained by:

- `THN_CLI_Command_Boundaries.md`
- `THN_CLI_Unified_History_Invariants_Ledger.md`
- `THN_CLI_Unified_History_Introspection_Surface_Index.md`
- `THN_Recovery_Authority_and_Invariants.md`
- `THN_CLI_DX2_Invariants.md`
- `THN_CLI_Diagnostics_Policy_Escalation.md`

Nothing in this document may weaken or reinterpret those guarantees.

---

## Change Policy

Any change to command authority requires:

1. Explicit documentation update
2. Changelog entry (intent and outcome)
3. Review of Unified History, Diagnostics, and Recovery invariants

Silent changes are prohibited.

---

## Summary

THN CLI command authority is:

- Explicit
- Bounded
- Non-inferential
- Non-escalating

Commands either **act**, **present**, or **observe**.

No command may silently cross that boundary.

End of document.

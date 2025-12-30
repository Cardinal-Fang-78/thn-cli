THN CLI – Sync V2 History & Diagnostics Contract
===============================================

Purpose
-------
This document defines the read-only diagnostic contract for Sync V2 execution
history exposed via the THN CLI.

It establishes:
  • What constitutes “history”
  • The authoritative data sources
  • The output shape and stability guarantees
  • Explicit non-goals and exclusions

This surface is intended for:
  • CLI users
  • Future GUI consumers
  • CI and audit tooling
  • Forensic and support workflows

It is not an execution or policy surface.


Command Surface
---------------
The Sync V2 history diagnostic is exposed via:

    thn sync history

This command is:
  • Read-only
  • Non-mutating
  • Policy-neutral
  • Deterministic in output ordering


Authoritative Data Sources
--------------------------
History entries are derived from:

  1. txlog (primary)
     • Append-only transaction records
     • Best-effort logging
     • May include partial or failed executions

  2. status_db (optional, read-only)
     • Authoritative long-term state
     • Used only to enrich history entries when available

The absence of status_db data must never be treated as an error.


Scope Definition
----------------
“History” represents **observed execution attempts**, not guaranteed state.

Included:
  • Successful applies
  • Failed applies
  • Dry-run executions
  • Diagnostic-only invocations where logged

Excluded:
  • Inferred executions
  • Filesystem reconstruction
  • Replay or rollback semantics
  • Policy evaluation results


Output Contract
---------------
The command emits **JSON only**.

Top-level structure:

{
    "status": "OK",
    "count": <int>,
    "limit": <int>,
    "entries": [ ... ]
}

Field meanings:
  • status
      – Always "OK" for successful command execution
  • count
      – Number of entries returned
  • limit
      – Applied cap on returned entries
  • entries
      – Ordered list of history records (most recent first)


Entry Shape
-----------
Each history entry is a **verbatim diagnostic record**, minimally normalized
for consumer stability.

Required fields:

{
    "tx_id": "<string>",
    "timestamp": "<ISO-8601>",
    "status": "OK" | "FAILED" | "DRY_RUN",
    "target": "<string>",
    "mode": "<string>",
    "dry_run": <bool>,
    "summary": { ... }
}

Notes:
  • timestamp ordering is authoritative
  • summary is diagnostic and non-normative
  • no field implies execution correctness


Ordering & Limits
-----------------
Entries are returned in **reverse chronological order** (most recent first).

Default limit:
  • 50 entries

Rationale:
  • Prevents unbounded output
  • Supports interactive use
  • Avoids accidental CI / log flooding
  • Can be raised later without contract breakage

If fewer than `limit` entries exist, all available entries are returned.


Stability Guarantees
--------------------
This diagnostic surface guarantees:

  • No mutation of engine state
  • No inferred or synthesized history
  • Stable field names and meanings
  • Additive-only evolution (new fields may be added)
  • No removal or repurposing of existing fields

Consumers must tolerate unknown additional fields.


Explicit Non-Goals
------------------
This command does NOT:
  • Enforce policy
  • Determine success semantics
  • Replace golden tests
  • Perform diffing or aggregation
  • Act as a recovery or replay tool

Any such behavior requires a separate, versioned contract.


Change Discipline
-----------------
Changes to this diagnostic surface require:
  • Documentation updates to this file
  • Explicit intent in CHANGELOG.md
  • Consumer impact review

Silent changes are treated as regressions.


Status
------
This document is normative.

Implementation must conform to this contract.

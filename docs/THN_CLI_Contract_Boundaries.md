THN CLI – Engine vs CLI Contract Boundaries
==========================================

Purpose
-------
This document defines the authoritative contract boundaries between the
THN Sync V2 engine and the CLI presentation layer.

It exists to:
  • Prevent semantic drift between engine behavior and CLI output
  • Clarify which output fields are authoritative vs legacy or diagnostic
  • Support long-term stability of golden tests, CI, and downstream consumers
  • Provide a durable reference for future refactors and extensions


Authority Model
---------------
The THN Sync V2 system is governed by a strict authority hierarchy:

  1. Engine (Authoritative)
     • Implements correctness, safety, and mutation semantics
     • Defines canonical result structures
     • Owns apply, validation, and rollback guarantees

  2. CLI (Presentation Boundary)
     • Surfaces engine results verbatim
     • Adds routing context, diagnostics, and destination resolution
     • Must not infer, reinterpret, or synthesize engine outcomes

  3. Diagnostics / Tooling
     • Read-only
     • Non-authoritative
     • Must never imply apply semantics


CLI Boundary Classification Registry
-----------------------------------
THN also enforces a command-level authority classification across the CLI surface.

The single authoritative registry is:
  thn_cli/contracts/cli_boundaries.py

This registry:
  • Classifies every top-level CLI command as authoritative, diagnostic, or presentation
  • Supports explicit path overrides for leaf commands when required
  • Is test-enforced to prevent silent authority drift

Policy:
  • This document does not duplicate command lists or tables from the registry.
  • Documentation must reference the registry to avoid divergence.
  • Any expansion of the CLI surface requires an accompanying registry update.


Golden Master Contract
----------------------
The authoritative JSON output surfaces for Sync V2 are defined in:

    docs/THN_CLI_Golden_Master_Spec.md

Golden tests bind to this specification and enforce:

  • Field presence and absence
  • Declarative (not inferred) semantics
  • Stability across platforms and Python versions
  • Explicit scoping of diagnostics


Field Classification
--------------------

### Authoritative Fields
These fields are owned by the engine and define observable behavior:

  • mode
  • operation
  • target
  • destination
  • routing
  • applied_count (apply only)
  • files (apply only)
  • backup_created
  • restored_previous_state

The CLI must surface these fields without reinterpretation.


### Diagnostic Fields
These fields provide visibility but do not affect correctness:

  • cdc_diagnostics
      – payload_completeness
      – other CDC inspection metadata

Diagnostics must:
  • Be explicitly labeled
  • Never imply success or failure
  • Never alter engine semantics


### Legacy Fields
The following fields exist for historical or compatibility reasons:

  • success

Policy:
  • Retained for backward compatibility
  • Treated as non-authoritative
  • Not relied upon by golden tests or future contracts
  • Subject to future deprecation under a versioned change

Consumers must not treat legacy fields as primary indicators of correctness.


Diagnostics Consumer Contracts
------------------------------
While this document defines **command and field authority**, it does not define
how diagnostic output may be *consumed*.

All guarantees governing diagnostic consumption — including non-enforcement,
tolerance of unknown fields, metadata non-semantics, and topology decoupling —
are defined in:

    docs/diagnostics_consumer_contracts.md

That document is authoritative for:
  • How diagnostic output may be parsed or stored
  • What consumers may and may not infer
  • Forward-compatibility and schema evolution rules

This separation is intentional:
  • Authority classification governs *what commands are*
  • Consumer contracts govern *how diagnostics may be used*

No diagnostic consumer behavior may contradict the guarantees defined there.


Prohibited Behaviors
--------------------
The following are explicitly disallowed:

  • CLI inferring apply results from filesystem inspection
  • CLI fabricating fields not present in engine output
  • Diagnostics being interpreted as apply outcomes
  • Tests binding to non-contractual or incidental fields
  • Silent output changes without Golden Master updates


Change Discipline
-----------------
Any change that affects:
  • Engine output shape
  • CLI JSON structure
  • Presence or absence of fields
  • Semantic meaning of existing fields

MUST be accompanied by:
  • An update to the Golden Master specification
  • Explicit golden test updates
  • A changelog entry describing intent and outcome

Uncoordinated changes are treated as regressions.


CLI Boundary Registry Governance
-------------------------------
The THN CLI maintains a single authoritative registry that classifies every
top-level command into one of three boundary classes:

  • Authoritative
  • Diagnostic
  • Presentation

This registry exists to prevent silent authority drift as the CLI evolves.
See also: thn_cli/command_loader.py for diagnostic-only loader warnings.

Governance Model
----------------
Boundary classification is enforced through a layered governance approach:

  • The registry itself defines the canonical boundary intent
  • Loader-time diagnostics warn if a registered command lacks classification
  • Tests enforce that no top-level command remains unclassified

Loader diagnostics are intentionally **non-blocking** and **non-enforcing**.
They exist solely to surface omissions early, without altering runtime behavior.

Design Principles
-----------------
  • No inference from filenames or imports
  • No automatic classification
  • No mutation or interception at runtime
  • No behavior changes without explicit documentation and changelog updates

This governance model ensures boundary intent remains explicit, auditable,
and stable across refactors, tooling changes, and future extensions.


Status
------
This document is normative.

It codifies existing behavior and does not introduce new semantics.

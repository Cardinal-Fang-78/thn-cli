THN CLI Error Contracts
======================

Purpose
-------
This document defines the **canonical error taxonomy and behavior** for the
THN CLI and all subordinate tooling.

It establishes guarantees around:
- Exit codes
- Error stability
- Rendering rules
- Prohibited behaviors

This document governs **errors only**.  
Diagnostics and command boundary authority are defined separately.

---

Guarantees
----------
The THN CLI enforces the following guarantees for all errors:

• Every error has a stable numeric exit code  
• Error kinds are immutable once released  
• Human-readable messages are always provided  
• Debug mode may expose additional metadata  
• No error causes automatic retries  

These guarantees apply across:
- CLI commands
- Developer tools
- CI execution
- GUI-facing wrappers

---

Error Taxonomy
--------------
Errors are classified by **kind**, not by message text.

The authoritative error kinds, exit codes, and semantics are defined in code
and enforced by tests.

This document intentionally **does not duplicate** tables or enums that are
owned by code.

Authoritative sources:
- `thn_cli/contracts/errors.py`
- `thn_cli/contracts/exceptions.py`

Any change to error kinds or exit codes requires:
- A code change
- Test updates
- A changelog entry

---

ErrorContract Semantics
----------------------
An error contract defines:

• The exit code  
• The error kind  
• The primary human-readable message  
• Optional suggestions  
• Optional debug-only context  

Errors are **terminal**:
- Execution stops immediately
- No implicit retries
- No corrective inference

---

Rendering Rules
---------------
Errors MUST be rendered in the following canonical form:

ERROR [code: KIND]: message text

Rules:
• The meaning line is always present  
• Suggestions are optional  
• Debug hints appear only in debug mode  
• JSON emission may reuse this contract  

Formatting is governed by:
- `thn_cli/contracts/formatting.py`

---

Diagnostics vs Errors
---------------------
Errors and diagnostics are intentionally separate concepts.

• Errors indicate failure and terminate execution  
• Diagnostics are read-only visibility surfaces  

Diagnostics taxonomy and structure are defined in:
- `thn_cli/diagnostics/diagnostic_result.py`
- `thn_cli/diagnostics/suite.py`

Diagnostics MUST NOT:
- Imply success or failure
- Alter exit codes
- Be treated as authoritative outcomes

---

Forbidden Practices
-------------------
The following behaviors are explicitly disallowed:

• Raising `SystemExit` directly  
• Printing stack traces outside debug mode  
• Reusing exit codes  
• Auto-correcting user input  
• Retrying implicitly  

Violations are treated as contract regressions.

---

Status
------
This document is normative.

It codifies existing behavior and does not introduce new semantics.

Sync V2 CDC Apply
Manifest-Derived Mutation Plan (Authoritative)

Status: LOCKED (Execution Semantics)
Scope: Sync V2 apply engine only
Applies to: cdc-delta mode (Stage 1 and Stage 2)

----------------------------------------------------------------------
1. Purpose
----------------------------------------------------------------------

Define a single, authoritative Mutation Plan derived from a CDC-delta
manifest, used by the Sync V2 engine BEFORE any apply occurs, to guarantee:

- Correct path-scoped backup
- Correct rollback on failure
- Deterministic execution semantics
- Stage-agnostic behavior (payload-based or chunk-based)
- Future replay, strict mode, and GC compatibility

This plan is execution infrastructure.
It is not diagnostics, not planning heuristics, and not storage logic.

----------------------------------------------------------------------
2. Core Principle
----------------------------------------------------------------------

The engine must never infer mutation scope from filesystem state or apply
behavior. Mutation scope is declared solely by the manifest.

The manifest is the single source of truth for receiver-side mutations.

----------------------------------------------------------------------
3. Definition: Mutation Plan
----------------------------------------------------------------------

A Mutation Plan is a normalized, stage-agnostic representation of all
filesystem mutations that MAY occur during CDC apply.

It is derived once, before apply, from the manifest, and is consumed by
the engine for:

- Backup creation
- Rollback
- Apply orchestration
- Future replay semantics

Conceptual shape:

    MutationPlan:
        writes:  Set[str]   # logical relative paths
        deletes: Set[str]   # logical relative paths

Rules:
- Paths are POSIX-style logical paths as declared in the manifest.
- Paths are relative to target.destination_path.
- The plan is complete and explicit.
- No filesystem inspection is permitted during derivation.

----------------------------------------------------------------------
4. Manifest to Mutation Plan Mapping (Authoritative)
----------------------------------------------------------------------

4.1 Stage 1 (payload-based CDC)

Manifest shape:
    manifest["files"] = [
        { "path": "a/b.txt", ... },
        ...
    ]

Mutation Plan:
    writes  = { f["path"] for f in manifest["files"] }
    deletes = ∅

Notes:
- Stage 1 is write-only.
- Rollback scope is limited to declared files only.
- Files not declared in the manifest are preserved across rollback.

----------------------------------------------------------------------
4.2 Stage 2 (chunk-based CDC)

Manifest shape:
    manifest["entries"] = [
        { "path": "x/y.txt", "op": "write", ... },
        { "path": "z/old.bin", "op": "delete" }
    ]

Mutation Plan:
    writes  = { e["path"] for e in entries if e["op"] == "write" }
    deletes = { e["path"] for e in entries if e["op"] == "delete" }

Notes:
- Write and delete are first-class mutations.
- Both MUST be covered by backup and rollback semantics.
- Rollback restores declared paths only.
- Unrelated files are not guaranteed to survive Stage 2 rollback.

----------------------------------------------------------------------
4.3 Invalid / Malformed CDC Manifests
----------------------------------------------------------------------

If neither manifest["files"] nor manifest["entries"] are present:

- Mutation Plan derivation fails.
- Apply MUST fail before any mutation or backup occurs.
- No backups are created.
- Error is authoritative and terminal.

This behavior is enforced by the engine and guarded by tests.

----------------------------------------------------------------------
5. Engine Responsibilities (Execution-Only)
----------------------------------------------------------------------

Once the Mutation Plan exists, the engine MUST:

1. Create path-scoped backups
   - Only for paths in writes ∪ deletes
   - Backup existing files only
   - Never back up entire destination trees

2. Apply mutations
   - Delegate mutation mechanics to delta.apply
   - Engine does not inspect or rewrite files itself

3. Roll back on failure
   - Restore backed-up paths only
   - Do not attempt to infer or reconstruct state

4. Commit success
   - TXLOG and Status DB are best-effort observers only

The engine MUST NOT:
- Infer paths from payload contents
- Infer paths from chunk lists
- Inspect destination directories to discover scope
- Delegate rollback responsibility to delta.apply or store

----------------------------------------------------------------------
6. Non-Goals (Explicit)
----------------------------------------------------------------------

This mutation plan does NOT:
- Compute deltas
- Validate chunk integrity
- Enforce signature policy
- Perform garbage collection
- Inspect filesystem state
- Participate in diagnostics

Those concerns belong to other layers.

----------------------------------------------------------------------
7. Diagnostic and Inspection Surfaces (Non-Authoritative)
----------------------------------------------------------------------

Helpers such as:

- inspect_cdc_mutation_plan()
- delta inspectors
- CLI inspection commands

MAY surface mutation intent for diagnostics and tooling, but:

- They MUST NOT influence execution behavior
- They are NOT authoritative
- They are NOT CLI-stable unless explicitly promoted

Only the engine-consumed Mutation Plan is authoritative.

----------------------------------------------------------------------
8. Rationale
----------------------------------------------------------------------

This design:
- Eliminates Stage 1 / Stage 2 divergence at the engine level
- Makes rollback semantics provable
- Enables future strict and replay modes without refactors
- Avoids shims, flags, or inference
- Keeps storage and apply layers simple and correct

There is no lower-cost alternative that preserves correctness.

----------------------------------------------------------------------
9. Internal Engine Notation (Recommended)
----------------------------------------------------------------------

Add the following comment-only notation near the top of
thn_cli/syncv2/engine.py:

    CDC APPLY SEMANTICS (LOCKED)
    For cdc-delta mode, the engine derives a manifest-declared Mutation Plan
    BEFORE apply:
        - Stage 1: manifest["files"]   -> writes
        - Stage 2: manifest["entries"] -> writes + deletes

    This plan is authoritative for:
        - Path-scoped backups
        - Rollback on failure
        - Deterministic execution semantics

    The engine MUST NOT infer mutation scope from filesystem state,
    payload contents, or chunk data.

    Reference:
        "Sync V2 CDC Apply – Manifest-Derived Mutation Plan (Authoritative)"

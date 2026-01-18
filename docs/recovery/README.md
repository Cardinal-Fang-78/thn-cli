# Recovery Documentation

This directory defines the **authority boundaries, invariants,
and non-goals** for recovery behavior in the THN CLI.

Recovery is **deliberate, explicit, and currently non-existent**.

---

## Definitions

- **Rollback**  
  Execution-local reversal of a failed operation  
  (covered under Sync V2 and CDC apply semantics)

- **Recovery**  
  Post-execution, user-initiated attempts to restore system state  
  (not implemented)

---

## Start Here

Key documents:

- **THN_Recovery_Authority_and_Invariants.md**  
  Canonical definition of what recovery is and is not.

- **THN_CLI_Recovery_Invariants_Ledger.md**  
  Non-negotiable recovery invariants and constraints.

- **THN_Recovery_Introspection_Surface_Index.md**  
  Exhaustive enumeration of where recovery must not occur.

---

## Status

No recovery behavior is implemented.

Any appearance of recovery behavior outside explicit,
versioned introduction is a defect.

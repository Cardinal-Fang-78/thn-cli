\# THN CLI Golden Master Contract



This document defines the Golden Master behavior contract for the THN CLI.



Once established, the Golden Master represents the canonical, user-visible

behavior of the CLI. Any deviation is considered intentional and must be

explicitly approved.



---



\## What the Golden Master Is



The Golden Master is a snapshot-based contract that locks:



• Exit codes  

• Standard output (stdout)  

• Standard error (stderr)  

• Error message wording and formatting  

• Help and version output  



These behaviors are validated via tests in:



&nbsp;   tests/golden/



and snapshot files in:



&nbsp;   tests/golden/snapshots/



---



\## What the Golden Master Is Not



The Golden Master does NOT freeze:



• Internal implementation details  

• Refactoring choices  

• Performance characteristics  

• Internal logging or tracing  

• Non user-visible behavior  



Only externally observable CLI behavior is covered.



---



\## Modification Rules



Golden snapshots MUST NOT be modified unless ALL of the following are true:



1\. A user-visible behavior change is intentional

2\. The change is reviewed and justified

3\. Snapshots are regenerated explicitly

4\. The change aligns with a versioned milestone



Accidental snapshot drift is treated as a regression.



---



\## Snapshot Regeneration



To intentionally update Golden Master snapshots:



Windows (cmd.exe):



&nbsp;   set THN\_UPDATE\_GOLDEN=1

&nbsp;   pytest tests/golden



POSIX shells:



&nbsp;   THN\_UPDATE\_GOLDEN=1 pytest tests/golden



Snapshot updates MUST be committed alongside the code changes

that justify them.



---



\## CI Enforcement



Golden Master tests are enforced in CI.



Any pull request that changes user-visible behavior without updating

snapshots will fail by design.



This is intentional.



---



\## Philosophy



The Golden Master exists to ensure:



• Stable UX guarantees  

• Predictable automation behavior  

• Safe refactoring over time  

• Confidence during long-term evolution  



Breaking the Golden Master is a decision, not an accident.

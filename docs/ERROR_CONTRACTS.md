\# THN CLI Error Contracts



This document defines the canonical error taxonomy and behavior

for the THN CLI and all subordinate tooling.



\## Guarantees



• Every error has a stable numeric exit code  

• Error kinds are immutable once released  

• Human-readable messages are always provided  

• Debug mode may expose additional metadata  

• No error causes automatic retries  



\## Atomic Error Types



<insert table>



\## ErrorContract Semantics



<insert semantics table>



\## Rendering Rules



• ERROR \[code: KIND]: <message>

• Meaning line is always present

• Suggestions are optional

• Debug hints are debug-only

• JSON emission may reuse this contract



\## Forbidden Practices



• Raising SystemExit directly

• Printing stack traces outside debug mode

• Reusing exit codes

• Auto-correcting user input

• Retrying implicitly

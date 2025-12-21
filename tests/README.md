\## Golden Test Contract



THN uses golden (snapshot-based) tests to lock CLI output behavior.



\### Update Mode



Golden snapshots are updated \*\*only\*\* when the following environment variable is set:



&nbsp;   THN\_UPDATE\_GOLDEN=1



When enabled:

\- Snapshot files are created or overwritten

\- Test output becomes the new baseline



\### Normal Mode (Default)



When unset or set to `0`:

\- CLI output is compared against existing snapshots

\- Any mismatch fails the test



\### Strict Naming Rule



The canonical environment variable is:



&nbsp;   THN\_UPDATE\_GOLDEN



The plural form `THN\_UPDATE\_GOLDENS` is \*\*not supported\*\* and will trigger an error

to prevent accidental misuse.



This strictness is intentional to preserve snapshot integrity.

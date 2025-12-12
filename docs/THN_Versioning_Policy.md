# THN CLI Semantic Versioning Policy (SVP)

## Table of Contents
- [1. MAJOR Version](#1-major-version-x00)
- [2. MINOR Version](#2-minor-version-xy0)
- [3. PATCH Version](#3-patch-version-xyz)
- [4. Governance Principles](#4-governance-principles)
- [5. Version Governance Matrix](#5-version-governance-matrix)
- [6. Release Workflow Summary](#6-release-workflow-summary)
- [7. Sync V2 Compatibility Rules](#7-sync-v2-compatibility-rules)
- [8. File Locations & Responsibilities](#8-file-locations--responsibilities)
- [9. Summary](#9-summary)



This document defines the authoritative versioning rules for the THN CLI.  

The single source of truth for the current version is stored in:



thn\_cli/\_\_init\_\_.py → \_\_version\_\_



The THN CLI uses Semantic Versioning (SemVer):



MAJOR.MINOR.PATCH



---



\# 1. MAJOR Version (X.0.0)



A MAJOR version increase occurs when a change breaks backward compatibility, including:



\- Removal or renaming of commands.

\- Required command flags changed or added.

\- Breaking changes in Sync V2 envelope or manifest schema.

\- Changes in routing-engine behavior that invalidate existing routing definitions.

\- Blueprint schema or template rules that break existing generators.

\- Plugin API contract changes.

\- Incompatible tenant schema changes.



Examples:

\- Sync envelope schema v2 → v3  

\- Changing required flags for a core command  

\- Breaking blueprint directory or naming expectations  



---



\# 2. MINOR Version (X.Y.0)



A MINOR version increase occurs when backward-compatible features are added:



\- New commands.

\- New optional flags for existing commands.

\- New blueprint templates or project generators.

\- New delta inspectors or sync analyzers.

\- Additional negotiation or diagnostics reporting.

\- New tenant types or tenant-aware features.

\- Performance improvements that do not change behavior.



Examples:

\- Add “thn sync analyze”  

\- Add optional --json or --verbose flags  

\- Add new Sync V2 inspectors  



---



\# 3. PATCH Version (X.Y.Z)



A PATCH version increase occurs when changes do not affect compatibility:



\- Bug fixes.

\- Crash fixes.

\- Logging or formatting corrections.

\- Stability improvements.

\- Documentation-only updates.

\- Internal refactors without behavior change.

\- Sync negotiation ordering fixes.

\- Delta inspector correctness fixes.



Examples:

\- Fix crash in commands\_sync\_web  

\- Fix incorrect envelope size reporting  

\- Improve routing fallback behavior  



---



\# 4. Governance Principles



1\. CLI behavior relied on by automation must remain stable across MINOR/PATCH.

2\. Sync V2 envelope and delta schema changes always require a MAJOR bump.

3\. Routing \& Blueprint engines define important behavioral contracts.

4\. Tenant schema evolution is version-governed:

&nbsp;  - Adding tenants → MINOR  

&nbsp;  - Changing tenant schema → MAJOR  



---



\# 5. Version Governance Matrix



| Change Type | Impact | Version |

|-------------|--------|---------|

| Add new CLI command | Additive | MINOR |

| Remove/rename command | Breaking | MAJOR |

| Optional command flag added | Compatible | MINOR |

| Required flag added | Breaking | MAJOR |

| Sync envelope schema change | Breaking | MAJOR |

| Add new delta inspector | Compatible | MINOR |

| Fix crash or bug | Compatible | PATCH |

| Update blueprint schema/template contract | Breaking | MAJOR |

| Add new blueprint template | Compatible | MINOR |

| Add new tenant type | Compatible | MINOR |

| Modify tenant schema | Breaking | MAJOR |



---



\# 6. Release Workflow Summary



1\. Update \_\_version\_\_ in thn\_cli/\_\_init\_\_.py  

2\. Run tests and static analysis  

3\. Update CHANGELOG.md  

4\. Generate release PDF  

5\. Publish to TestPyPI  

6\. Validate installation  

7\. Push tag to trigger PyPI publishing and release notes  



---



\# 7. Sync V2 Compatibility Rules



MAJOR bump required for:

\- Envelope schema changes  

\- Manifest field additions/removals  

\- Chunk format changes  

\- Negotiation protocol revisions  



MINOR bump used when:

\- Optional metadata added  

\- New inspectors or tools added  



PATCH bump used when:

\- Crashes fixed  

\- Negotiation logging corrected  

\- Stability improvements made  



---



\# 8. File Locations \& Responsibilities



\- Version source → thn\_cli/\_\_init\_\_.py  

\- Version policy → docs/THN\_Versioning\_Policy.md  

\- Changelog → CHANGELOG.md  

\- Release Checklist → docs/RELEASE\_CHECKLIST.md  

\- Release PDFs → out/ or attached to GitHub Releases  

\- Version tooling → tools/  



---



\# 9. Summary



The THN CLI version governs compatibility across:



\- Sync V2 envelopes and delta operations  

\- Routing engine behavior  

\- Blueprint engine  

\- Plugin architecture  

\- Tenant-aware behavior  

\- Release automation  



Follow:

\- PATCH for safety  

\- MINOR for growth  

\- MAJOR for evolution  




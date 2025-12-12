---

title: THN CLI Versioning Policy

nav\_order: 10

---



\# THN CLI Semantic Versioning Policy



> This page describes how THN CLI versions evolve and how compatibility is maintained across Sync V2, routing, blueprints, delta operations, plugins, and tenant systems.



---



\## Version Source Location



The authoritative version string is stored here:



\*\*`thn\_cli/\_\_init\_\_.py → \_\_version\_\_`\*\*



THN CLI uses:



\*\*MAJOR.MINOR.PATCH\*\*



---



\## MAJOR (X.0.0)



Breaking changes that require incompatible updates:



\- Removed or renamed commands  

\- Required flags changed  

\- Sync V2 envelope/manifest schema change  

\- Routing engine behavioral changes  

\- Blueprint schema changes  

\- Plugin API contract changes  

\- Tenant schema incompatibility  



---



\## MINOR (X.Y.0)



Backwards-compatible feature additions:



\- New commands  

\- New optional flags  

\- New blueprint templates  

\- New inspectors or sync analyzers  

\- New tenants  

\- Performance improvements  



---



\## PATCH (X.Y.Z)



No compatibility impact:



\- Bug fixes  

\- Crash fixes  

\- Logging corrections  

\- Internal refactors  

\- Documentation updates  



---



\## Governance Matrix



| Change Type                            | Version |

|----------------------------------------|---------|

| Add new command                        | MINOR   |

| Remove/rename command                  | MAJOR   |

| Add optional flag                      | MINOR   |

| Add required flag                      | MAJOR   |

| Sync envelope schema change            | MAJOR   |

| New delta inspector                    | MINOR   |

| Crash fix                              | PATCH   |

| Blueprint schema change                | MAJOR   |

| Add new tenant                         | MINOR   |

| Change tenant schema                   | MAJOR   |



---



\## Release Workflow



1\. Update `\_\_version\_\_`  

2\. Run tests + static analysis  

3\. Update CHANGELOG  

4\. Generate Release PDF  

5\. Publish to TestPyPI  

6\. Validate  

7\. Tag release (→ Publish to PyPI)  



---



\## Sync V2 Compatibility Rules



\- Envelope schema changes → \*\*MAJOR\*\*  

\- Optional metadata additions → \*\*MINOR\*\*  

\- Crash/stability fixes → \*\*PATCH\*\*  



---



\## Summary



Versioning governs compatibility for:



\- Sync V2 envelopes  

\- Routing engine  

\- Blueprint engine  

\- Plugin system  

\- Tenant-aware operations  

\- Automated release pipelines  



Follow:



\- \*\*PATCH → Safe fixes\*\*  

\- \*\*MINOR → Growth\*\*  

\- \*\*MAJOR → Evolution\*\*  




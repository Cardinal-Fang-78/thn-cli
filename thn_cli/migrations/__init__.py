"""
THN CLI – Scaffold Migration System (Hybrid)

Hybrid model:
- Declarative migration specs (JSON) define deterministic filesystem transforms
- Optional Python hooks handle complex logic when needed
- Engine performs in-place upgrades with atomic manifest updates

Primary concepts:
- Blueprint identity: {id, version}
- Migration: from -> to (same blueprint id), composed of steps
- Steps: mkdir, touch, write_json, delete, hook
"""

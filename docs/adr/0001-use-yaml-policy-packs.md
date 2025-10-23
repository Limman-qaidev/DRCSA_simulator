# ADR 0001: YAML policy packs

- **Status:** Accepted
- **Date:** 2024-05-17

## Context

The simulator requires structured regulatory datasets comprising risk weights, LGD tables, product
mappings and hedging parameters.  The data is sourced from supervisory manuals and updated on a
quarterly basis.  We need a format that is easy to review, version control and hash for audit
purposes.

## Decision

Policy datasets are stored as YAML files under `drc_sa_calculator/regdata/<policy>` and loaded via
`PolicyDataLoader`.  Each policy bundle contains `risk_weights.yaml`, `lgd_tables.yaml`,
`hedging_rules.yaml` and `mappings.yaml`.  Files are validated for schema correctness, parsed into
in-memory dictionaries and accompanied by SHA-256 hashes that are emitted in the computation
response payloads.

## Consequences

- YAML keeps policy updates human-readable and diff friendly, so regulatory analysts can propose
  changes via pull requests.
- Hashes can be embedded in exports, helping downstream risk systems assert the exact policy
  revision used during calculation.
- Runtime loading is fast enough for the application profile, but large future datasets might
  require caching or compiled artefacts.

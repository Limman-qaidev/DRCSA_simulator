# API Overview

The DRCSA simulator exposes a FastAPI application that provides read/write operations for
regulatory datasets, scenarios and calculation results.  All endpoints emit JSON and are documented
by the generated OpenAPI specification at `/openapi.json`.

## Authentication

No authentication is enforced in the reference deployment.  Service operators should front the API
with their preferred gateway when deploying into secured environments.

## Health check

`GET /health`
: Returns `{ "status": "ok" }` when the application is ready to serve requests.

## Dataset catalogue

`GET /datasets/policies`
: Returns the list of policy identifiers bundled with the service (for example
  `"BCBS_MAR"`, `"EU_CRR3"`).

`GET /datasets/policies/{policy}`
: Returns the SHA-256 hashes of the policy artefacts used when computing capital charges.  These
  hashes are embedded in exported computation results so downstream systems can verify regulatory
  lineage.

## Scenario management

`GET /scenarios`
: Lists the scenarios currently stored in the in-memory registry.

`GET /scenarios/{name}`
: Retrieves a full scenario definition, including exposures, descriptions and tags.  This endpoint
  is typically used by user interfaces to populate scenario editors or to export baseline data for
  reconciliation.

`PUT /scenarios/{name}`
: Creates or replaces a scenario.  Payloads are validated according to the rules in
  `drc_sa_calculator/domain/rules.py` (positive notionals, currencies, and unique trade IDs).  The
  endpoint returns the canonical scenario representation that will be used by subsequent compute
  calls.

`DELETE /scenarios/{name}`
: Removes a scenario from the registry.

## Computation service

`POST /compute`
: Executes the DRCSA calculator for the supplied policy, baseline scenario and any number of
  alternate scenarios.  The response contains

  - `result` – structured totals including per-exposure capital charges, aggregate scenario
    statistics and the policy metadata; and
  - `comparisons` – optional deltas versus the baseline (enabled by default via
    `include_comparisons=true`).

Clients can persist the response to downstream systems as a complete export of the computation
inputs and outputs.

## Reference data mirrors

`GET /reference/policies/{policy}/mappings`
: Returns the product-to-exposure routing tables for the policy.

`GET /reference/policies/{policy}/hedges`
: Returns hedging rule metadata including supervisory parameters.

`GET /reference/policies/{policy}/risk-weights`
: Returns the hierarchical exposure risk weight structure used by the calculator.

`GET /reference/policies/{policy}/lgd`
: Returns the LGD tables for the policy.  Consumers can use the data to reconcile LGD lookups and
  to construct user interfaces for manual overrides.

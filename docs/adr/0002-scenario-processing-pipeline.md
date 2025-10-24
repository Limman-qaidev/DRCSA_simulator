# ADR 0002: Scenario processing pipeline

- **Status:** Accepted
- **Date:** 2024-05-17

## Context

Users submit baseline and alternative scenarios through both an API and a graphical UI.  The
platform must validate inputs, compute capital charges, produce comparisons and make the same
information available for export to downstream systems.  Multiple delivery channels (REST, CLI,
UI) should share a single business logic implementation.

## Decision

We centralised processing inside `DRCSACalculationEngine`, which accepts immutable domain models and
returns structured results (`ScenarioResult`, `ScenarioComparison`, `ScenarioMatrix`).  API routers,
CLI commands and UI components convert external payloads into these domain objects before invoking
the engine.  A singleton `InMemoryScenarioStore` keeps working scenarios available to both compute
requests and the UI without persisting data to disk.

## Consequences

- The domain engine can be unit-tested independently of transport concerns, improving confidence in
  JTD and aggregation logic.
- Additional delivery channels (for example a batch processor) only need thin adapters that marshal
  data into domain models.
- The in-memory store keeps the example deployment lightweight but will require replacement with a
  durable repository in production environments.

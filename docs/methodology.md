# Methodology

This document captures the quantitative approach implemented in the DRCSA simulator.  It is
intended to serve as a bridge between the Basel Committee on Banking Supervision (BCBS)
references – specifically the **Market Risk – Standardised Approach** (MAR, October 2023
consolidated text) – and the executable logic in `drc_sa_calculator`.

## Risk metric derivation

The simulator targets the jump-to-default (JTD) component of the Default Risk Charge (DRC).
The capital charge for a single exposure is derived from three inputs:

- **Notional exposure** \(N_i\) measured in reporting currency.
- **Risk weight** \(w_i\) supplied by the applicable regulatory policy (for example the BCBS
  MAR standardised exposure table in `regdata/BCBS_MAR/risk_weights.yaml`).
- **Loss given default** \(\mathrm{LGD}_i\) when provided in the policy `lgd_tables.yaml`.  If no LGD
  is supplied the MAR paragraphs 186-188 allow the risk-weight-only charge to stand.

The jump-to-default capital charge for exposure *i* is therefore

$$
\mathrm{JTD}_i = N_i \times w_i \times \max\left(1, \mathrm{LGD}_i \right)^{\mathbb{I}[\mathrm{LGD}_i \text{ present}]}
$$

In practice the implementation keeps the expression linear by setting \(\mathrm{LGD}_i = 1\) when no
LGD table applies.  The relevant logic appears in
`drc_sa_calculator/domain/engine/calculator.py::_compute_exposure` where the resolved LGD either
scales the risk weighted notional or defaults to unity.

For a scenario \(S\) containing exposures \(E\) the aggregate charge is the sum of individual
exposures:

$$
\mathrm{Charge}(S) = \sum_{i \in E} \mathrm{JTD}_i.
$$

This additive treatment is consistent with BCBS MAR paragraph 186, which aggregates net jump-to-
default amounts before applying the hedging caps.

## Policy lookups

Risk weights, LGD tables, hedging parameters and product mappings are parameterised via policy
packages under `drc_sa_calculator/regdata`.  Each policy directory mirrors the BCBS annex
structure:

- `risk_weights.yaml` – exposure class hierarchy and associated weights.
- `lgd_tables.yaml` – optional LGD overrides per exposure class or quality step.
- `mappings.yaml` – product-to-exposure routing tables and counterparty grade lookups.
- `hedging_rules.yaml` – supervisory correlations for cross-bucket netting.

The loader (`PolicyDataLoader`) validates payloads for schema compliance and calculates SHA-256
hashes that become part of the computation metadata.  This ensures export payloads capture which
regulatory policy version drove the numbers, satisfying audit requirements in MAR paragraph 26.

## Scenario validation

Prior to computation each scenario is validated for structural consistency:

1. **Positive notionals** – exposures with non-positive notional are rejected (MAR paragraph 182).
2. **Currency presence** – the reporting currency must be explicitly supplied so conversion rules
   can be applied upstream of the simulator.
3. **Unique trade identifiers** – duplicate `trade_id` entries produce deterministic errors to avoid
   double counting.

These constraints are implemented in `domain/rules.py` and enforced at both API ingestion and the
CLI, ensuring invalid payloads cannot progress to aggregation.

## Edge-case handling

Several defensive behaviours protect the calculation from ambiguous inputs:

- **Missing exposure classification** – if an exposure lacks `exposure_class` and the policy has no
  mapping for the provided `product_type`, the calculator raises a
  `RiskWeightResolutionError`.  This propagates to the API caller so upstream systems can correct
  the payload.
- **Absent quality step** – the engine attempts to infer quality from `product_type` or
  `counterparty_grade` before failing, mirroring the MAR requirement to use the bank’s credit
  assessment hierarchy.
- **LGD fallbacks** – when a specific LGD grade is missing, the calculator searches progressively
  through the quality-step path (e.g. `large_bank/senior`) and then any policy-wide grade entries.
  This matches BCBS guidance on using the most conservative available LGD.
- **Scenario aggregation** – scenario totals and comparisons (`ScenarioMatrix`, `compare_scenarios`)
  treat missing exposures in alternates as zero contribution deltas, preventing misleading swings
  when a trade is absent from a scenario.

Together these rules guarantee that exported computation results can be reconciled to regulatory
expectations while providing deterministic failure modes for incomplete data feeds.

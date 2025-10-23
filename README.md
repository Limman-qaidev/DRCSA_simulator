# DRCSA_simulator

Default Risk Charge (Standardised Approach) calculator prototype providing:

* **FastAPI service** under ``drc_sa_calculator.app`` with OpenAPI 3.1 compliant
  endpoints for loading regulatory datasets, managing scenarios and triggering
  computations.
* **NiceGUI front-end** under ``drc_sa_calculator.ui`` covering the required
  user flows (Data Loader, Baseline, Scenario Builder, Scenario Matrix and
  Compare View).
* **Domain layer** with typed models, validation rules, computation engine and
  comparison utilities in ``drc_sa_calculator.domain``.
* **Typer-based CLI** exposed as ``drcsa`` for running batch computations with
  policy provenance metadata in the output.

## Development

Install the package in editable mode:

```bash
pip install -e .
```

Run the FastAPI application using Uvicorn:

```bash
uvicorn drc_sa_calculator.app.main:app --reload
```

Launch the NiceGUI front-end (assumes the API is running locally on
``http://localhost:8000``):

```bash
python -m drc_sa_calculator.ui.server
```

Execute the CLI against a scenario definition JSON file:

```bash
drcsa compute ./scenario.json --policy BCBS_MAR
```

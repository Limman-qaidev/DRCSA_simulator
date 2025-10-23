"""Policy data loading utilities."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

import yaml


class PolicyDataValidationError(ValueError):
    """Raised when policy data fails validation checks."""


@dataclass(frozen=True)
class PolicyData:
    """Container for policy specific regulatory datasets."""

    name: str
    risk_weights: Mapping[str, Any]
    lgd_tables: Mapping[str, Any]
    hedging_rules: Mapping[str, Any]
    mappings: Mapping[str, Any]
    hashes: Mapping[str, str]

    def table(self, name: str) -> Mapping[str, Any]:
        """Return one of the policy tables by attribute name."""

        if not hasattr(self, name):
            raise KeyError(f"Unknown policy table '{name}'")
        return getattr(self, name)


class PolicyDataLoader:
    """Loads regulatory policy datasets from YAML files."""

    DATASETS: Mapping[str, str] = {
        "risk_weights": "risk_weights.yaml",
        "lgd_tables": "lgd_tables.yaml",
        "hedging_rules": "hedging_rules.yaml",
        "mappings": "mappings.yaml",
    }

    def __init__(self, base_path: Path | None = None) -> None:
        self._base_path = base_path or Path(__file__).resolve().parents[2] / "regdata"

    def available_policies(self) -> Iterable[str]:
        """Return the list of available policy directories."""

        if not self._base_path.exists():
            return []
        return sorted(
            entry.name
            for entry in self._base_path.iterdir()
            if entry.is_dir() and not entry.name.startswith(".")
        )

    def load(self, policy_name: str) -> PolicyData:
        """Load and validate regulatory datasets for a policy."""

        policy_path = self._base_path / policy_name
        if not policy_path.is_dir():
            raise PolicyDataValidationError(
                f"Policy directory '{policy_name}' not found under {self._base_path}"
            )

        data: Dict[str, Mapping[str, Any]] = {}
        hashes: Dict[str, str] = {}

        for table_name, file_name in self.DATASETS.items():
            file_path = policy_path / file_name
            payload = self._load_yaml(file_path)
            validator = getattr(self, f"_validate_{table_name}")
            data[table_name] = validator(payload)
            hashes[table_name] = self._compute_hash(payload)

        hashes["policy"] = self._compute_hash({key: data[key] for key in sorted(data)})

        return PolicyData(
            name=policy_name,
            risk_weights=data["risk_weights"],
            lgd_tables=data["lgd_tables"],
            hedging_rules=data["hedging_rules"],
            mappings=data["mappings"],
            hashes=hashes,
        )

    @staticmethod
    def _load_yaml(path: Path) -> Mapping[str, Any]:
        if not path.is_file():
            raise PolicyDataValidationError(f"Missing required dataset file: {path}")
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
        if not isinstance(loaded, Mapping):
            raise PolicyDataValidationError(f"Dataset in {path} must be a mapping")
        return loaded

    @staticmethod
    def _compute_hash(data: Mapping[str, Any]) -> str:
        canonical = json.dumps(_sort_structure(data), separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _validate_versioned_payload(name: str, payload: Mapping[str, Any]) -> None:
        version = payload.get("version")
        if not isinstance(version, str) or not version.strip():
            raise PolicyDataValidationError(f"{name} requires a non-empty 'version' field")

    def _validate_risk_weights(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        self._validate_versioned_payload("risk_weights", payload)
        exposures = payload.get("exposures")
        if not isinstance(exposures, Mapping):
            raise PolicyDataValidationError("risk_weights must define an 'exposures' mapping")
        _validate_numeric_mapping("risk_weights.exposures", exposures)
        return payload

    def _validate_lgd_tables(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        self._validate_versioned_payload("lgd_tables", payload)
        table = payload.get("lgd")
        if not isinstance(table, Mapping):
            raise PolicyDataValidationError("lgd_tables must define an 'lgd' mapping")
        _validate_numeric_mapping("lgd_tables.lgd", table)
        return payload

    def _validate_hedging_rules(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        self._validate_versioned_payload("hedging_rules", payload)
        hedges = payload.get("hedges")
        if not isinstance(hedges, Mapping):
            raise PolicyDataValidationError("hedging_rules must define a 'hedges' mapping")
        for risk_class, buckets in hedges.items():
            if not isinstance(buckets, Mapping):
                raise PolicyDataValidationError(
                    f"hedging_rules '{risk_class}' buckets must be mappings"
                )
            for bucket, rules in buckets.items():
                if not isinstance(rules, Mapping):
                    raise PolicyDataValidationError(
                        f"hedging_rules '{risk_class}.{bucket}' must be a mapping"
                    )
                instruments = rules.get("eligible_instruments")
                if not isinstance(instruments, list) or not instruments:
                    raise PolicyDataValidationError(
                        f"hedging_rules '{risk_class}.{bucket}' requires a non-empty eligible_instruments list"
                    )
                if any(not isinstance(item, str) for item in instruments):
                    raise PolicyDataValidationError(
                        f"hedging_rules '{risk_class}.{bucket}' instruments must be strings"
                    )
                for key, value in rules.items():
                    if key == "eligible_instruments":
                        continue
                    if not isinstance(value, (int, float)):
                        raise PolicyDataValidationError(
                            f"hedging_rules '{risk_class}.{bucket}.{key}' must be numeric"
                        )
        return payload

    def _validate_mappings(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        self._validate_versioned_payload("mappings", payload)
        product_mappings = payload.get("product_mappings")
        if not isinstance(product_mappings, Mapping):
            raise PolicyDataValidationError(
                "mappings must define a 'product_mappings' mapping"
            )
        for product, mapping in product_mappings.items():
            if not isinstance(mapping, Mapping):
                raise PolicyDataValidationError(
                    f"mappings for product '{product}' must be a mapping"
                )
            exposure = mapping.get("exposure")
            quality = mapping.get("quality_step")
            if not isinstance(exposure, str) or not exposure:
                raise PolicyDataValidationError(
                    f"mappings '{product}' requires a non-empty exposure string"
                )
            if not isinstance(quality, str) or not quality:
                raise PolicyDataValidationError(
                    f"mappings '{product}' requires a non-empty quality_step string"
                )
        counterparty_grades = payload.get("counterparty_grades")
        if not isinstance(counterparty_grades, Mapping) or not counterparty_grades:
            raise PolicyDataValidationError(
                "mappings must define a non-empty 'counterparty_grades' mapping"
            )
        for grade, target in counterparty_grades.items():
            if not isinstance(grade, str) or not isinstance(target, str):
                raise PolicyDataValidationError(
                    "counterparty_grades must map grade strings to target strings"
                )
        return payload


def _validate_numeric_mapping(path: str, payload: Mapping[str, Any]) -> None:
    for key, value in payload.items():
        current_path = f"{path}.{key}"
        if isinstance(value, Mapping):
            _validate_numeric_mapping(current_path, value)
        elif isinstance(value, (int, float)):
            continue
        else:
            raise PolicyDataValidationError(
                f"{current_path} must resolve to a numeric value or mapping"
            )


def _sort_structure(data: Any) -> Any:
    if isinstance(data, Mapping):
        return {key: _sort_structure(data[key]) for key in sorted(data)}
    if isinstance(data, list):
        return [_sort_structure(item) for item in data]
    return data

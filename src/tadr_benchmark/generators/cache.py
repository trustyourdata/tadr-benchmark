"""Verified working-source reuse; all generation and hashing precede analyze."""

from pathlib import Path

from ..models import DatasetArtifact, ScenarioSpec
from ..paths import contained
from ..scenarios.expectations import expectations_for
from ..scenarios.recipe import Recipe
from ..serialization import canonical_bytes, sha256
from ..execution.ledger import write_once
from .identity import logical_dataset_sha256, source_file_sha256
from .tabular import iter_rows
from .writers import (AlphaDatasetGenerator, logical_schema, read_logical_source, read_source_schema)


def verify_source(root: Path, scenario: ScenarioSpec, artifact: DatasetArtifact) -> None:
    expectations_for(scenario)
    recipe = Recipe.model_validate(scenario.generator_parameters)
    source = contained(root, artifact.relative_path)
    if artifact.scenario_sha256 != sha256(canonical_bytes(scenario)):
        raise ValueError("cached scenario provenance mismatch")
    if artifact.ground_truth != scenario.ground_truth():
        raise ValueError("cached independent ground truth mismatch")
    schema = logical_schema(recipe)
    if read_source_schema(source, recipe.representation) != schema:
        raise ValueError("cached logical schema mismatch")
    if source_file_sha256(source) != artifact.source_file_sha256:
        raise ValueError("cached source checksum mismatch")
    expected = logical_dataset_sha256(schema, iter_rows(recipe), recipe.row_count)
    decoded = logical_dataset_sha256(schema, read_logical_source(source, recipe.representation), recipe.row_count)
    if expected != decoded or expected != artifact.logical_dataset_sha256:
        raise ValueError("cached logical dataset checksum mismatch")


def materialize(root: Path, scenario: ScenarioSpec) -> DatasetArtifact:
    receipt = contained(root, f".work/datasets/{scenario.scenario_id}.artifact.json")
    if receipt.exists():
        artifact = DatasetArtifact.model_validate_json(receipt.read_bytes())
        verify_source(root, scenario, artifact)
        return artifact
    artifact = AlphaDatasetGenerator().generate(scenario, root)
    write_once(receipt, canonical_bytes(artifact))
    return artifact

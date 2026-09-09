"""Exact report comparisons, with dedicated preregistered format eligibility."""

import json
from copy import deepcopy
from typing import Literal

from ..models import Contract, Digest, Identifier, RunResult, ScenarioSpec, TargetMetadata
from ..serialization import sha256


class ExactComparison(Contract):
    comparison_version: Literal["1.0"] = "1.0"
    left_run_id: Identifier
    right_run_id: Identifier
    comparison_kind: Literal["determinism", "string_format", "native_projection"]
    eligible: bool
    ineligibility_reasons: list[str]
    left_report_sha256: Digest
    right_report_sha256: Digest
    canonical_bytes_equal: bool
    first_difference_path: str | None
    semantic_projection_equal: bool | None = None
    semantic_first_difference_path: str | None = None
    field_agreement: dict[str, bool]


def first_difference(left, right, path="$") -> str | None:
    if type(left) is not type(right):
        return path
    if isinstance(left, dict):
        for key in sorted(left.keys() | right.keys()):
            child = path + "[" + json.dumps(key, ensure_ascii=False) + "]"
            if key not in left or key not in right:
                return child
            difference = first_difference(left[key], right[key], child)
            if difference:
                return difference
    elif isinstance(left, list):
        for i, (a, b) in enumerate(zip(left, right)):
            difference = first_difference(a, b, f"{path}[{i}]")
            if difference:
                return difference
        if len(left) != len(right):
            return f"{path}[{min(len(left), len(right))}]"
    elif left != right:
        return path
    return None


def _reports(left, right, originals):
    a, b = originals[left.run_id], originals[right.run_id]
    if sha256(a) != left.canonical_report_sha256 or sha256(b) != right.canonical_report_sha256:
        raise ValueError("comparison report checksum mismatch")
    return a, b, json.loads(a), json.loads(b)


def _compare(left, right, originals, kind, reasons, *, projection=None):
    a, b, pa, pb = _reports(left, right, originals)
    fields = ("findings", "readiness_score", "report_confidence", "total_risk", "category_risks",
              "score_breakdown", "dataset_profile", "analysis_stats", "remediation_plan")
    return ExactComparison(left_run_id=left.run_id, right_run_id=right.run_id, comparison_kind=kind,
        eligible=not reasons, ineligibility_reasons=reasons, left_report_sha256=sha256(a), right_report_sha256=sha256(b),
        canonical_bytes_equal=a == b, first_difference_path=None if a == b else first_difference(pa, pb) or "$bytes",
        field_agreement={f: pa.get(f) == pb.get(f) for f in fields},
        semantic_projection_equal=None if reasons or projection is None else projection(pa) == projection(pb),
        semantic_first_difference_path=None if reasons or projection is None else first_difference(projection(pa), projection(pb)))


def compare_determinism(left: RunResult, right: RunResult, originals: dict[str, bytes]) -> ExactComparison:
    fields = (*TargetMetadata.model_fields, "campaign_id", "scenario_id", "scenario_version", "scenario_sha256",
              "logical_dataset_sha256", "source_file_sha256", "benchmark_git_commit", "benchmark_package_version",
              "analysis_variant", "constraints", "environment_id", "instrumentation_policy")
    if any(getattr(left, f) != getattr(right, f) for f in fields):
        raise ValueError("determinism requires the same source and provenance")
    return _compare(left, right, originals, "determinism", [])


def native_projection(report: dict) -> dict:
    projection = deepcopy(report)
    for column in projection["dataset_profile"]["columns"]:
        column["top_values"] = [{k: v for k, v in item.items() if k != "value"}
                                for item in column.get("top_values", [])]
    return projection


def compare_formats(left: RunResult, right: RunResult, left_scenario: ScenarioSpec,
                    right_scenario: ScenarioSpec, originals: dict[str, bytes]) -> ExactComparison:
    from ..scenarios.recipe import Recipe, recipe_from_id
    from ..scenarios.expectations import make_scenario
    for run, scenario in ((left, left_scenario), (right, right_scenario)):
        from ..serialization import canonical_bytes
        if run.scenario_sha256 != sha256(canonical_bytes(scenario)) or run.scenario_id != scenario.scenario_id:
            raise ValueError("format scenario binding mismatch")
        if scenario != make_scenario(recipe_from_id(scenario.scenario_id)):
            raise ValueError("format pair is not preregistered")
    lr, rr = Recipe.model_validate(left_scenario.generator_parameters), Recipe.model_validate(right_scenario.generator_parameters)
    if lr.representation != "csv" or rr.representation not in {"pqstr", "pqnative"}:
        raise ValueError("format pair must be CSV to approved Parquet representation")
    fields = set(Recipe.model_fields) - {"scenario_id", "representation"}
    if any(getattr(lr, f) != getattr(rr, f) for f in fields):
        raise ValueError("format pair constructions differ")
    dimensions = (*TargetMetadata.model_fields, "campaign_id", "benchmark_git_commit", "benchmark_package_version",
                  "analysis_variant", "constraints", "determinism_context", "environment_id", "phase", "repeat_index",
                  "task_type", "row_count", "column_count", "instrumentation_policy")
    if any(getattr(left, f) != getattr(right, f) for f in dimensions):
        raise ValueError("format pair execution provenance differs")
    reasons = []
    if left.analysis_mode != right.analysis_mode or left.sample_ratio != right.sample_ratio:
        reasons.append("mode_or_selected_population_differs")
    if rr.representation == "pqstr":
        if left.logical_dataset_sha256 != right.logical_dataset_sha256:
            raise ValueError("string format pair logical identity differs")
        return _compare(left, right, originals, "string_format", reasons)
    if lr.family != "scale":
        raise ValueError("native projection is confined to scale")
    _, _, a, b = _reports(left, right, originals)
    ca, cb = a["dataset_profile"]["columns"], b["dataset_profile"]["columns"]
    # Recipe equality establishes intended ordered values/nulls; the common fixed
    # sampling policy and equal mode/ratio establish selected positions.
    if [(c["name"], c["inferred_type"]) for c in ca] != [(c["name"], c["inferred_type"]) for c in cb]:
        reasons.append("inferred_types_differ")
    return _compare(left, right, originals, "native_projection", reasons, projection=native_projection)

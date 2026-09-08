import json

import pytest
from pydantic import ValidationError

from tadr_benchmark.campaigns.loader import load_campaign
from tadr_benchmark.models import CampaignManifest, GroundTruth, RunResult, ScenarioSpec, TargetMetadata
from tadr_benchmark.serialization import canonical_bytes
from tadr_benchmark.validation import planned_runs, validate_completed


@pytest.mark.parametrize("change", [{"status": "unknown"}, {"scenario_ids": ["a", "a"]},
                                    {"target_git_commit": "main"}, {"benchmark_git_commit": "main"},
                                    {"repeat_policy": None}, {"extra": 1}, {"python_version": None}])
def test_campaign_rejects_invalid_execution_metadata(campaign, change):
    with pytest.raises(ValidationError):
        CampaignManifest.model_validate({**campaign.model_dump(), **change})


@pytest.mark.parametrize("change", [{"row_count": "10"}, {"row_count": True}, {"row_count": 0},
                                    {"seed": 1}, {"source_format": "xlsx"},
                                    {"expected_numeric_score": 100}, {"task_parameters": {"task_type": "analytics"}}])
def test_scenario_is_strict_and_explicit(scenario, change):
    with pytest.raises(ValidationError):
        ScenarioSpec.model_validate({**scenario.model_dump(), **change})


def test_conflicting_ground_truth_is_rejected(scenario):
    data = scenario.ground_truth().model_dump()
    item = {"id_pattern": "quality.*", "subject": None}
    with pytest.raises(ValidationError):
        GroundTruth.model_validate({**data, "expected_findings": [item], "expected_absent_findings": [item]})


@pytest.mark.parametrize("change", [{"peak_rss_bytes": -1}, {"runtime_seconds": float("nan")},
                                    {"sample_ratio": 1.1}, {"readiness_score": 101},
                                    {"throughput_rows_per_second": 999.0}, {"target_git_commit": None},
                                    {"finding_ids": ["one"]}, {"result_schema_version": "2.0"}])
def test_run_result_rejects_invalid_records(completed, change):
    with pytest.raises(ValidationError):
        RunResult.model_validate({**completed[0][0].model_dump(), **change})


def test_target_urls_reject_credentials_and_local_targets(campaign):
    data = {field: getattr(campaign, field) for field in TargetMetadata.model_fields}
    for url in ("file:" + "/local", "https://" + "user:credential" + "@example.org/repo", "https://localhost/repo"):
        with pytest.raises(ValidationError):
            TargetMetadata.model_validate({**data, "target_repository_url_or_null": url})


def test_serialization_sorts_objects_preserves_semantic_arrays():
    assert canonical_bytes({"b": 2, "a": [2, 1]}) == canonical_bytes({"a": [2, 1], "b": 2})
    assert json.loads(canonical_bytes({"a": [2, 1]}))["a"] == [2, 1]


def test_duplicate_yaml_keys_are_rejected(tmp_path):
    path = tmp_path / "campaign.yaml"
    path.write_text("status: planned\nstatus: frozen\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_campaign(path)


def test_complete_plan_and_relational_validation(campaign, scenario, completed, environment):
    runs, _ = completed
    assert len(planned_runs(campaign, [scenario])) == 3
    validate_completed(campaign, [scenario], runs, {environment.environment_id: environment})
    for invalid in (runs[:-1], runs + [runs[0]]):
        with pytest.raises(ValueError, match="runs"):
            validate_completed(campaign, [scenario], invalid, {environment.environment_id: environment})


def test_json_round_trip(campaign, scenario, completed):
    for model in (campaign, scenario, completed[0][0]):
        assert type(model).model_validate_json(canonical_bytes(model)) == model


def test_dataset_drift_between_repeats_is_rejected(campaign, scenario, completed, environment):
    runs = list(completed[0])
    runs[0] = RunResult.model_validate({**runs[0].model_dump(), "source_file_sha256": "f" * 64})
    with pytest.raises(ValueError, match="same generated dataset"):
        validate_completed(campaign, [scenario], runs, {environment.environment_id: environment})

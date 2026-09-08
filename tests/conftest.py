"""Tiny fabricated harness fixtures; these are never campaign measurements."""

from pathlib import Path

import pytest

from tadr_benchmark.campaigns.loader import load_campaign
from tadr_benchmark.evaluation.detection import evaluate
from tadr_benchmark.models import CampaignManifest, EnvironmentInfo, RunResult, ScenarioSpec, TargetMetadata
from tadr_benchmark.serialization import canonical_bytes, sha256
from tadr_benchmark.validation import planned_runs


@pytest.fixture
def scenario():
    return ScenarioSpec(
        scenario_id="fixture.clean", scenario_version="1.0", description="Harness contract fixture only",
        task_type="analytics", task_parameters={}, row_count=10, column_count=2, source_format="csv",
        generator="fixture.sequence", generator_version="1.0", generator_parameters={},
        rng_algorithm=None, seed=None, defects=[], tags=["fixture"], expected_findings=[],
        expected_absent_findings=[], expected_affected_columns=[], expected_gate_behavior="none",
        rationale="Constructed fixture with no asserted defects; no target execution.")


@pytest.fixture
def campaign(scenario):
    planned = load_campaign(Path(__file__).parents[1] / "campaigns" / "ALPHA_BENCHMARK_V1.yaml")
    return CampaignManifest.model_validate({
        **planned.model_dump(), "campaign_id": "FIXTURE_V1", "status": "ready",
        "execution_groups": [], "execution_readiness": None,
        "scale_matrix": [10], "scenario_ids": [scenario.scenario_id],
        "benchmark_git_commit": "b" * 40, "python_version": "3.11.0",
        "reproducibility_status": "target_unavailable",
        "repeat_policy": {"warmup_runs": 1, "measurement_runs": 2},
        "instrumentation_policy": {"protocol_version": "1.0", "timeout_seconds": 60.0,
                                   "memory_sampling_interval_seconds": 0.01},
        "analysis_variants": [{"variant_id": "full_reference", "constraints": {}}],
        "determinism_cases": [{"case_id": "standard", "python_hash_seed": 0, "timezone": "UTC",
                               "decimal_precision": 28, "decimal_rounding": "ROUND_HALF_EVEN"}]})


@pytest.fixture
def environment():
    return EnvironmentInfo(os="Linux", os_version="6.0", architecture="x86_64", python_version="3.11.0",
                           cpu_model=None, physical_cpu_count=2, logical_cpu_count=4,
                           total_memory_bytes=1024, dependency_versions={"tadr-benchmark": "0.1.0", "tadr-core": "0.1.0"})


@pytest.fixture
def completed(campaign, scenario, environment):
    report = canonical_bytes({"readiness_score": 100, "report_confidence": 100, "total_risk": "0",
                              "category_risks": {"quality": "0"}, "findings": [],
                              "score_breakdown": {"caps_applied": []}, "remediation_plan": [],
                              "analysis_stats": {"row_count": 10, "col_count": 2,
                                                 "analysis_mode": "full", "sample_ratio": "1"}})
    runs = []
    reports = {}
    for spec in planned_runs(campaign, [scenario]):
        run = RunResult(
            **{field: getattr(campaign, field) for field in TargetMetadata.model_fields},
            **spec.model_dump(), logical_dataset_sha256="d" * 64, source_file_sha256="c" * 64,
            benchmark_git_commit=campaign.benchmark_git_commit,
            benchmark_package_version=campaign.benchmark_package_version,
            task_type="analytics", source_format="csv", row_count=10, column_count=2,
            analysis_mode="full", sample_ratio=1.0, runtime_seconds=2.0, throughput_rows_per_second=5.0,
            peak_rss_bytes=100, readiness_score=100, report_confidence=100, total_risk=0.0,
            category_risks={"quality": 0.0}, finding_ids=[], finding_subjects=[], finding_severities=[],
            hard_gates=[], remediation_ids=[], expected_finding_ids_or_patterns=[],
            detection_outcome=evaluate(scenario.ground_truth(), [], [], []),
            canonical_report_sha256=sha256(report), environment_id=environment.environment_id)
        runs.append(run)
        reports[run.run_id] = report
    return runs, reports


@pytest.fixture(autouse=True)
def prohibit_live_target_import(monkeypatch):
    """Phase 1 tests may mock adapter transport but must never load the target."""
    import builtins
    original = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name == "tadr" or name.startswith("tadr."):
            raise AssertionError("Live target imports are forbidden in Phase 1 software tests")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", guarded)

import pytest

from tadr_benchmark.evaluation.detection import evaluate
from tadr_benchmark.evaluation.sampling import compare_sampling
from tadr_benchmark.models import GroundTruth, RunResult
from tadr_benchmark.reporting.aggregate import aggregate, run_bytes
from tadr_benchmark.reporting.comparison import compare
from tadr_benchmark.reporting.figures import runtime_rows, write_runtime_figure
from tadr_benchmark.reporting.markdown import campaign_report
from tadr_benchmark.reporting.tables import summary_csv


def change(run, **fields):
    return RunResult.model_validate({**run.model_dump(), **fields})


def test_missed_defects_are_research_outcomes():
    truth = GroundTruth(expected_findings=[{"id_pattern": "quality.*", "subject": "column:x"}],
                        expected_absent_findings=[{"id_pattern": "schema.*", "subject": None}],
                        expected_affected_columns=["x"], expected_gate_behavior="none",
                        rationale="Independently constructed defect")
    result = evaluate(truth, ["schema.test::column:x"], ["column:x"], [])
    assert result.missed_expectations == [0]
    assert result.violated_absent_expectations == [0]
    assert result.gate_expectation_met is True


def test_aggregate_excludes_warmups_and_is_order_independent(campaign, completed):
    runs, _ = completed
    runs = [change(run, runtime_seconds=100.0, throughput_rows_per_second=0.1)
            if run.phase == "warmup" else run for run in runs]
    summary = aggregate(campaign.campaign_id, runs)
    assert summary == aggregate(campaign.campaign_id, list(reversed(runs)))
    assert summary.groups[0].runtime_median_seconds == 2.0
    assert summary.groups[0].measured_runs == 2
    assert run_bytes(runs) == run_bytes(list(reversed(runs)))
    assert "runtime_mad_seconds" in summary_csv(summary)
    assert "2" in campaign_report(campaign, summary)


def test_determinism_failure_is_preserved(campaign, completed):
    runs, _ = completed
    measured = next(run for run in runs if run.phase == "measurement")
    changed = [change(run, canonical_report_sha256="e" * 64) if run == measured else run for run in runs]
    assert aggregate(campaign.campaign_id, changed).groups[0].deterministic is False


def test_figure_query_and_svg_are_stable(campaign, completed, tmp_path):
    summary = aggregate(campaign.campaign_id, completed[0])
    assert runtime_rows(summary)[0][1] == 2.0
    first, second = tmp_path / "first.svg", tmp_path / "second.svg"
    write_runtime_figure(summary, first)
    write_runtime_figure(summary, second)
    assert first.read_bytes() == second.read_bytes()


def test_performance_requires_explicit_environment_approval(completed):
    run = next(run for run in completed[0] if run.phase == "measurement")
    other = change(run, run_id="second", runtime_seconds=1.0, throughput_rows_per_second=10.0,
                   environment_id="a" * 64)
    result = compare(run, other)
    assert result.detection_comparable
    assert not result.performance_comparable
    assert result.runtime_delta_percent is None
    approved = {run.environment_id: "controlled-host-class", other.environment_id: "controlled-host-class"}
    result = compare(run, other, approved)
    assert result.runtime_delta_percent == -50.0
    assert result.throughput_delta_percent == 100.0


@pytest.mark.parametrize("field,value", [("scenario_version", "2.0"), ("scenario_sha256", "e" * 64),
                                         ("source_format", "parquet"), ("constraints", {"max_memory_mb": 100})])
def test_semantic_mismatch_blocks_comparison(completed, field, value):
    run = next(run for run in completed[0] if run.phase == "measurement")
    result = compare(run, change(run, **{field: value}))
    assert not result.detection_comparable
    assert result.finding_agreement is None


def test_sampling_fidelity_has_separate_eligibility(completed):
    run = next(run for run in completed[0] if run.phase == "measurement")
    sample = change(run, run_id="sampled", analysis_variant="HEAD_STRIDE_V1",
                    analysis_mode="sampled", sample_ratio=0.5, readiness_score=90)
    comparison = compare_sampling(run, sample)
    assert comparison.readiness_score_delta == -10.0
    assert comparison.finding_agreement == 1.0
    with pytest.raises(ValueError):
        compare_sampling(sample, run)

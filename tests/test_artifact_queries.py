import json

import pytest

from tadr_benchmark.evaluation.exact import compare_formats
from tadr_benchmark.execution.attempts import make_attempt
from tadr_benchmark.models import RunResult
from tadr_benchmark.reporting.plots import build_figures, figure_queries
from tadr_benchmark.reporting.queries import ReportInputs, TABLE_COLUMNS, build_tables
from tadr_benchmark.scenarios.expectations import make_scenario
from tadr_benchmark.scenarios.recipe import recipe_from_id
from tadr_benchmark.serialization import canonical_bytes, sha256


def test_all_table_names_and_selected_only_queries(campaign, scenario, completed):
    runs, reports = completed
    inputs = ReportInputs(campaign, [scenario], runs, [], reports, [make_attempt(r) for r in runs])
    tables = build_tables(inputs)
    assert set(tables) == set(TABLE_COLUMNS) and len(tables) == 15
    assert tables == build_tables(ReportInputs(campaign, [scenario], list(reversed(runs)), [], reports,
                                              list(reversed(inputs.attempts))))
    assert b"denominator" in tables["detection_by_check.csv"]
    assert b"fixture.clean" in tables["identity.csv"]
    assert len(tables["remediation.csv"].splitlines()) == 1
    with pytest.raises(ValueError, match="nonsequential"):
        build_tables(ReportInputs(campaign, [scenario], runs, [], reports, [*inputs.attempts, inputs.attempts[0]]))


def test_approved_figure_queries_render_deterministically_in_temporary_files(tmp_path):
    # Deliberately tiny software-only rows, never passed off as Alpha observations.
    rows = {name: [] for name in TABLE_COLUMNS}
    rows["detection_by_check.csv"] = [dict(severity_cutoff="INFO", track="normative", format="csv",
        analysis_variant="full_reference", stratum="fixture", check_id="fixture.check", conditional_recall_numerator=1,
        evaluable_positive_opportunities=2, planned_positive_opportunities=3, terminal_target_failures=1)]
    rows["clean_false_positives.csv"] = [dict(finding_count=1, stratum="fixture", severity_cutoff="INFO", scenario_id="fixture.clean",
        track="normative", format="csv", successful_reports=1, planned_reports=1, unevaluable_negative_opportunities=0)]
    rows["score_sweeps.csv"] = [dict(family=f, case="fixture", format="csv", count=1, readiness_score=80)
                                for f in ("missing", "duplicate", "class", "leak")]
    rows["scale_performance.csv"] = [dict(task="analytics", format="csv", column_count=2, row_count=10,
        analysis_mode="full", runtime_median_seconds=1.0, peak_rss_median_bytes=100, throughput_median_rows_per_second=10.0)]
    rows["sampling_fidelity.csv"] = [dict(scenario_id="fixture.sampling", readiness_score_delta=-1, finding_agreement=0.5)]
    first, second = build_figures(rows), build_figures(rows)
    assert len(first) == 11 and first == second
    for name, data in first.items():
        (tmp_path / name).write_bytes(data)
        assert b"<svg" in data and b"dc:date" not in data
    rows["clean_false_positives.csv"][0]["finding_count"] = 0
    assert "clean_false_positives.svg" not in figure_queries(rows)


def format_fixture(base, scenario, run_id, report):
    original = canonical_bytes(report)
    result = RunResult.model_validate({**base.model_dump(), "run_id": run_id, "scenario_id": scenario.scenario_id,
        "scenario_sha256": sha256(canonical_bytes(scenario)), "task_type": scenario.task_type,
        "source_format": scenario.source_format, "row_count": scenario.row_count, "column_count": scenario.column_count,
        "throughput_rows_per_second": scenario.row_count/base.runtime_seconds,
        "canonical_report_sha256": sha256(original)})
    return result, original


def test_string_format_comparison_requires_preregistered_pair_and_preserves_mismatch(completed):
    base = next(r for r in completed[0] if r.phase == "measurement")
    left_scenario = make_scenario(recipe_from_id("leak.control.support49.csv"))
    right_scenario = make_scenario(recipe_from_id("leak.control.support49.pqstr"))
    report = json.loads(completed[1][base.run_id])
    report["analysis_stats"].update(row_count=49, col_count=left_scenario.column_count)
    left, a = format_fixture(base, left_scenario, "format.csv", report)
    right, b = format_fixture(base, right_scenario, "format.pqstr", report)
    comparison = compare_formats(left, right, left_scenario, right_scenario, {left.run_id: a, right.run_id: b})
    assert comparison.eligible and comparison.canonical_bytes_equal
    report["readiness_score"] = 99
    right, b = format_fixture(base, right_scenario, "format.pqstr", report)
    comparison = compare_formats(left, right, left_scenario, right_scenario, {left.run_id: a, right.run_id: b})
    assert comparison.eligible and not comparison.canonical_bytes_equal
    assert comparison.first_difference_path == '$["readiness_score"]'
    altered = RunResult.model_validate({**right.model_dump(), "logical_dataset_sha256": "f"*64})
    with pytest.raises(ValueError, match="logical"):
        compare_formats(left, altered, left_scenario, right_scenario, {left.run_id: a, right.run_id: b})


def test_native_format_inferred_type_mismatch_is_visible_ineligibility(completed):
    base = next(r for r in completed[0] if r.phase == "measurement")
    a_scenario = make_scenario(recipe_from_id("scale.analytics.n10000.w20.csv"))
    b_scenario = make_scenario(recipe_from_id("scale.analytics.n10000.w20.pqnative"))
    report = json.loads(completed[1][base.run_id])
    report["analysis_stats"].update(row_count=10000, col_count=20)
    report["dataset_profile"] = {"columns": [{"name": "x", "inferred_type": "numeric", "top_values": []}]}
    left, a = format_fixture(base, a_scenario, "native.csv", report)
    report["dataset_profile"]["columns"][0]["inferred_type"] = "categorical"
    right, b = format_fixture(base, b_scenario, "native.parquet", report)
    comparison = compare_formats(left, right, a_scenario, b_scenario, {left.run_id: a, right.run_id: b})
    assert not comparison.eligible
    assert comparison.ineligibility_reasons == ["inferred_types_differ"]
    assert comparison.semantic_projection_equal is None

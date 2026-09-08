"""Software-only opportunities and reports, never campaign observations."""

from dataclasses import replace

import pytest

from tadr_benchmark.companions import ScenarioExpectations
from tadr_benchmark.evaluation.metrics import (DetectionMetrics, Opportunity, TARGET_FAILURE_CATEGORIES,
    aggregate_detection, evaluate_frame, ratio)
from tadr_benchmark.execution.attempts import make_attempt
from tadr_benchmark.models import CampaignManifest, RunResult
from tadr_benchmark.reporting.plots import figure_queries
from tadr_benchmark.reporting.queries import ReportInputs, TABLE_COLUMNS, table_rows
from tadr_benchmark.serialization import canonical_bytes, sha256
from tadr_benchmark.validation import planned_runs


def opportunity(index, positive=True, track="controlled_condition", subject="column:x"):
    return Opportunity(opportunity_id=f"fixture.{index}.{track}.{subject.replace(':', '.')}",
        scenario_id=f"fixture.{index}", physical_defect_id="fixture.defect" if track == "controlled_condition" else None,
        track=track, check_id="fixture.check", subject=subject, positive=positive, stratum="fixture",
        matching_check_ids=["fixture.check"])


def report(detected):
    return {"findings": [{"id": "fixture.check::column:x", "severity": "HIGH", "metadata": {
        "check_id": "fixture.check", "subject_key": "column:x"}}] if detected else []}


def test_fifty_planned_example_separates_conditional_recall_coverage_and_yield():
    observations = [evaluate_frame([opportunity(i)], report(i < 45) if i < 47 else None,
        failure_kind=None if i < 47 else TARGET_FAILURE_CATEGORIES[i-47])[0] for i in range(50)]
    result = aggregate_detection(observations)
    assert (result.tp, result.fn, result.fp, result.tn) == (45, 2, 0, 0)
    assert result.conditional_recall == ratio(45, 47)
    assert result.conditional_precision == ratio(45, 45)
    assert result.conditional_fpr == ratio(0, 0)
    assert result.successful_report_coverage == ratio(47, 50)
    assert result.end_to_end_detection_yield == ratio(45, 50)
    assert (result.planned_opportunities, result.evaluable_opportunities, result.unevaluable_opportunities) == (50, 47, 3)
    assert result.successful_reports == 47 and result.terminal_target_failures == 3
    assert result.finding_evaluation == "PARTIALLY_EVALUABLE"
    assert result == aggregate_detection(list(reversed(observations)))


@pytest.mark.parametrize("kind", TARGET_FAILURE_CATEGORIES)
def test_terminal_failures_are_unevaluable_for_positive_and_negative_opportunities(kind):
    frame = [opportunity(0), opportunity(0, False, subject="column:z")]
    result = evaluate_frame(frame, None, failure_kind=kind)[0]
    assert (result.tp, result.fp, result.fn, result.tn) == (0, 0, 0, 0)
    assert result.finding_evaluation == "UNEVALUABLE"
    assert result.conditional_recall == result.conditional_precision == result.conditional_fpr == ratio(0, 0)
    assert result.successful_report_coverage == ratio(0, 2)
    assert result.positive_successful_report_coverage == result.negative_successful_report_coverage == ratio(0, 1)
    assert result.end_to_end_detection_yield == ratio(0, 1)
    assert result.terminal_target_failures_by_category[kind] == 1
    assert sum(result.terminal_target_failures_by_category.values()) == 1
    assert not result.mapped_detector_details
    successful_empty = evaluate_frame(frame, report(False))[0]
    assert successful_empty.fn == successful_empty.tn == 1
    assert successful_empty.successful_report_coverage == ratio(2, 2)


def test_normative_info_cutoff_changes_class_support_without_changing_report_availability():
    frame = [opportunity(0, track="normative").model_copy(update={"severity": "INFO"})]
    inclusive = evaluate_frame(frame, None, failure_kind="timeout")[0]
    actionable = evaluate_frame(frame, None, cutoff="LOW", failure_kind="timeout")[0]
    assert inclusive.unevaluable_positive_opportunities == actionable.unevaluable_negative_opportunities == 1
    assert inclusive.end_to_end_detection_yield is actionable.end_to_end_detection_yield is None
    assert inclusive.successful_report_coverage == actionable.successful_report_coverage == ratio(0, 1)


def test_infrastructure_is_operational_and_pending_cells_are_explicit():
    with pytest.raises(ValueError, match="infrastructure"):
        evaluate_frame([opportunity(0)], None, failure_kind="infrastructure")
    with pytest.raises(ValueError):
        evaluate_frame([opportunity(0)], report(True), failure_kind="timeout")
    pending = evaluate_frame([opportunity(0)], None)[0]
    assert pending.pending_reports == 1 and pending.terminal_target_failures == 0 and pending.fn == 0
    assert pending.end_to_end_detection_yield == ratio(0, 1)


def test_coverage_schema_rejects_false_support_or_failure_as_prediction():
    result = evaluate_frame([opportunity(0)], None, failure_kind="timeout")[0]
    for changes in ({"fn": 1}, {"planned_opportunities": 0}, {"finding_evaluation": "EVALUABLE"},
                    {"successful_report_coverage": ratio(1, 1).model_dump()}):
        with pytest.raises(ValueError):
            DetectionMetrics.model_validate({**result.model_dump(), **changes})


@pytest.fixture
def coverage_inputs(campaign, scenario, completed):
    from test_attempt_ledger import interrupted
    from test_outcomes import failure
    other = scenario.model_copy(update={"scenario_id": "fixture.failed"})
    scenarios = [scenario, other]
    manifest = CampaignManifest.model_validate({**campaign.model_dump(), "scenario_ids": [s.scenario_id for s in scenarios]})
    runs = [RunResult.model_validate({**completed[0][0].model_dump(), **spec.model_dump()})
            for spec in planned_runs(manifest, scenarios)]
    failed_run = next(r for r in runs if r.scenario_id == other.scenario_id and r.phase == "measurement" and r.repeat_index == 0)
    failed = failure(failed_run, failure_kind="timeout", error_code="deadline_exceeded", exception_class=None,
                     elapsed_seconds=60.0, policy_limit=60.0)
    successful = [r for r in runs if r != failed_run]
    reports = {r.run_id: completed[1][completed[0][0].run_id] for r in successful}
    attempts = [make_attempt(r) for r in [*successful, failed]]
    selected = next(r for r in successful if r.scenario_id == scenario.scenario_id and r.phase == "measurement" and r.repeat_index == 0)
    attempts = [a for a in attempts if a.run_id != selected.run_id] + [
        make_attempt(interrupted(selected), resolution_code="harness_fixed"), make_attempt(selected, index=1)]
    labels = [ScenarioExpectations(scenario_id=s.scenario_id, scenario_version=s.scenario_version,
        scenario_sha256=sha256(canonical_bytes(s)), physical={"scenario_id": s.scenario_id, "row_count": 10,
        "column_names": ["x", "z"], "conditions": []}, normative=[{"variant_id": "full_reference", "findings": [],
        "absent_check_ids": ["fixture.check"], "gates": []}], primary_clean_control_eligible=True) for s in scenarios]
    frames = {(s.scenario_id, "full_reference"): [opportunity(i, False, track, subject) for track in ("normative", "controlled_condition")
        for subject in (["column:x"] if i == 0 else ["column:x", "column:z"])] for i, s in enumerate(scenarios)}
    return ReportInputs(manifest, scenarios, successful, [failed], reports, attempts, labels, opportunities=frames)


def test_tables_count_planned_opportunities_not_reports_repeats_or_retry_attempts(coverage_inputs):
    tables = table_rows(coverage_inputs)
    detection = tables["detection_by_check.csv"]
    assert len(detection) == 4  # Two tracks and two cutoffs, independently.
    for row in detection:
        assert (row["tp"], row["fp"], row["fn"], row["tn"]) == (0, 0, 0, 1)
        assert row["conditional_fpr_denominator"] == 1 and row["conditional_fpr"] == 0
        assert row["planned_negative_opportunities"] == 3 and row["unevaluable_negative_opportunities"] == 2
        assert row["successful_report_coverage"] == 1/3  # Opportunity-weighted, not 1/2 reports.
        assert row["successful_reports"] == 1 and row["planned_reports"] == 2
        assert row["terminal_target_failures_by_category"]["timeout"] == 1
        assert row["terminal_target_failures"] == 1 and row["pending_reports"] == 0
    missing = [r for r in tables["clean_false_positives.csv"] if r["scenario_id"] == "fixture.failed"]
    assert len(missing) == 4
    for row in missing:
        assert row["finding_evaluation"] == "UNEVALUABLE" and row["finding_count"] is None and row["finding_ids"] is None
        assert row["conditional_fpr"] is None and row["conditional_fpr_denominator"] == 0
        assert row["planned_negative_opportunities"] == row["unevaluable_negative_opportunities"] == 2
        assert row["readiness_score"] is None and row["scenario_denominator"] == 0
    matrix = next(r for r in tables["scenario_matrix.csv"] if r["scenario_id"] == "fixture.failed")["scenario_metrics"]["full_reference"]
    assert matrix["normative_conformant"] is None and matrix["gates_and_suppression"] is None
    assert matrix["normative"]["scenario_detection"]["denominator"] == 0


def test_partial_queries_retain_missing_planned_cells(coverage_inputs):
    missing_id = coverage_inputs.failures[0].run_id
    partial = replace(coverage_inputs, failures=[], attempts=[a for a in coverage_inputs.attempts if a.run_id != missing_id])
    for row in table_rows(partial)["detection_by_check.csv"]:
        assert row["planned_opportunities"] == 3 and row["evaluable_opportunities"] == 1
        assert row["unevaluable_opportunities"] == 2 and row["pending_reports"] == 1 and row["terminal_target_failures"] == 0


def test_detection_figure_carries_coverage_and_yield_even_when_all_reports_fail():
    tables = {name: [] for name in TABLE_COLUMNS}
    tables["detection_by_check.csv"] = [dict(track="controlled_condition", check_id="fixture.check", stratum="fixture",
        format="csv", analysis_variant="full_reference", severity_cutoff="INFO", conditional_recall_numerator=0,
        evaluable_positive_opportunities=0, planned_positive_opportunities=3, terminal_target_failures=3)]
    query = figure_queries(tables)["detection_by_check.svg"]
    assert len(query.points) == 2
    assert all(point[2] == 0 and "0/3" in point[1] for point in query.points)
    assert any("coverage" in p[0] for p in query.points) and any("end-to-end detection yield" in p[0] for p in query.points)
    assert not any("conditional recall" in p[0] for p in query.points)


def test_frozen_fixture_preserves_unevaluable_coverage_and_rejects_rechecksummed_rate_changes(tmp_path, monkeypatch, campaign, environment):
    import csv
    from test_attempt_ledger import monitor
    from tadr_benchmark.campaigns import freeze as publication
    from tadr_benchmark.companions import DatasetIdentity, RunFailure
    from tadr_benchmark.generators.writers import logical_schema
    from tadr_benchmark.models import TargetMetadata
    from tadr_benchmark.scenarios.expectations import expectations_for, make_scenario
    from tadr_benchmark.scenarios.recipe import recipe_from_id
    recipe = recipe_from_id("leak.control.support49.csv")
    scenario = make_scenario(recipe)
    manifest = CampaignManifest.model_validate({**campaign.model_dump(), "scenario_ids": [scenario.scenario_id],
        "scale_matrix": [49], "repeat_policy": {"warmup_runs": 0, "measurement_runs": 1}})
    spec = planned_runs(manifest, [scenario])[0]
    failed = RunFailure(**spec.model_dump(), **{k: getattr(manifest, k) for k in TargetMetadata.model_fields},
        benchmark_git_commit=manifest.benchmark_git_commit, benchmark_package_version=manifest.benchmark_package_version,
        environment_id=environment.environment_id, logical_dataset_sha256="d"*64, source_file_sha256="c"*64,
        failure_kind="timeout", stage="analyze", error_code="deadline_exceeded", exception_class=None,
        independently_validated_input=True, adjudication="valid_target_outcome", elapsed_seconds=60.0, policy_limit=60.0)
    instrument = monitor(failed).model_copy(update={"terminal_state": "failure"})
    dataset = DatasetIdentity(scenario_id=scenario.scenario_id, scenario_version=scenario.scenario_version,
        scenario_sha256=spec.scenario_sha256, logical_dataset_sha256="d"*64, source_file_sha256="c"*64,
        logical_schema=logical_schema(recipe), row_count=49, writer_policy={"representation": "csv"})
    monkeypatch.setattr(publication, "require_clean_revision", lambda *args: manifest.benchmark_git_commit)
    monkeypatch.setattr(publication, "repository_issues", lambda *args, **kwargs: [])
    directory = publication.freeze(tmp_path, manifest, [scenario], [], {environment.environment_id: environment}, {},
        "2026-01-01", public_reviewed=True, failures=[failed], attempts=[make_attempt(failed, instrumentation=instrument)],
        expectations=[expectations_for(scenario)], datasets=[dataset], instrumentation=[instrument])
    publication.verify_frozen(directory)
    table = directory / "tables" / "detection_by_check.csv"
    rows = list(csv.DictReader(table.read_text().splitlines()))
    positive = next(r for r in rows if r["track"] == "controlled_condition" and int(r["planned_positive_opportunities"]) > 0)
    assert positive["fn"] == "0" and positive["conditional_recall"] == "" and positive["conditional_recall_denominator"] == "0"
    assert positive["successful_report_coverage"] == "0.0" and positive["end_to_end_detection_yield"] == "0.0"
    assert positive["finding_evaluation"] == "UNEVALUABLE" and positive["terminal_target_failures"] == "1"
    report_text = (directory / "REPORT.md").read_text()
    assert "UNEVALUABLE" in report_text and "planned/evaluable/unevaluable" in report_text
    assert "conditional_recall" in (directory / "protocol.md").read_text()
    positive["conditional_recall"] = "1.0"
    with table.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    inventory = sorted(p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file() and p.name != "checksums.sha256")
    (directory / "checksums.sha256").write_text("".join(sha256((directory / name).read_bytes())+"  "+name+"\n" for name in inventory))
    with pytest.raises(ValueError, match="derived table is stale"):
        publication.verify_frozen(directory)

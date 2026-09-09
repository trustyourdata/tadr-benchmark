import json
from dataclasses import replace

import pytest

from tadr_benchmark.companions import DiagnosticValue
from tadr_benchmark.evaluation.exact import compare_determinism, first_difference, native_projection
from tadr_benchmark.evaluation.metrics import Opportunity, evaluate_frame, ratio
from tadr_benchmark.execution.diagnostics import extract_metrics
from tadr_benchmark.execution.executor import successful_result
from tadr_benchmark.execution.supervisor import Invocation, invoke_worker
from tadr_benchmark.generators.cache import materialize
from tadr_benchmark.models import RunResult, RunSpec
from tadr_benchmark.scenarios.expectations import make_scenario
from tadr_benchmark.scenarios.recipe import recipe_from_id
from tadr_benchmark.serialization import sha256


def test_cache_recounts_logical_data_and_rejects_source_corruption(tmp_path):
    scenario = make_scenario(recipe_from_id("leak.control.support49.csv"))
    original = materialize(tmp_path, scenario)
    assert materialize(tmp_path, scenario) == original
    path = tmp_path / original.relative_path
    path.write_bytes(path.read_bytes().replace(b"1000", b"1001", 1))
    with pytest.raises(ValueError, match="checksum"):
        materialize(tmp_path, scenario)


def test_exact_comparison_preserves_byte_only_mismatch(completed):
    runs, reports = completed
    left, right = runs[:2]
    changed = reports[right.run_id] + b"\n"
    right = RunResult.model_validate({**right.model_dump(), "canonical_report_sha256": sha256(changed)})
    comparison = compare_determinism(left, right, {left.run_id: reports[left.run_id], right.run_id: changed})
    assert not comparison.canonical_bytes_equal
    assert comparison.first_difference_path == "$bytes"
    assert all(comparison.field_agreement.values())
    assert first_difference({"a": [1, 2]}, {"a": [1, 3]}) == '$["a"][1]'


def test_native_projection_removes_only_value_encoding():
    report = {"dataset_profile": {"columns": [{"name": "x", "top_values": [{"value": {"kind": "int"}, "count": 2}]}]}}
    projected = native_projection(report)
    assert projected["dataset_profile"]["columns"][0]["top_values"] == [{"count": 2}]
    assert "value" in report["dataset_profile"]["columns"][0]["top_values"][0]


def test_diagnostic_allowlist_does_not_export_arbitrary_bundle_fields():
    values = extract_metrics({"column_diagnostics": {"signal_x": {"canonical_attempts": 10,
        "canonical_failures": 2, "private_detail": "unstructured"}}, "arbitrary": "unstructured"}, "parse")
    assert values["parse_failures"] == DiagnosticValue(value=2.0, unavailable_reason=None)
    assert values["missing_count"].unavailable_reason == "not_applicable"
    assert values["nonmissing_count"].unavailable_reason == "not_exposed"
    assert "arbitrary" not in values and "private_detail" not in values


def test_fixed_denominators_wrong_subject_and_separate_tracks():
    def opportunity(identity, track, subject, positive, severity=None):
        return Opportunity(opportunity_id=identity, track=track, check_id="schema.parse_failures",
            subject=subject, positive=positive, severity=severity, stratum="boundary",
            matching_check_ids=["schema.parse_failures"])
    frame = [opportunity("norm.x", "normative", "column:x", True, "LOW"),
             opportunity("norm.z", "normative", "column:z", False),
             opportunity("physical.x", "controlled_condition", "column:x", True)]
    report = {"findings": [{"id": "f.z", "severity": "low",
        "metadata": {"check_id": "schema.parse_failures", "subject_key": "column:z"}}]}
    physical, normative = evaluate_frame(frame, report)
    assert (normative.tp, normative.fp, normative.fn, normative.tn) == (0, 1, 1, 0)
    assert normative.conditional_fpr == ratio(1, 1)
    assert normative.localization == ratio(0, 1)
    assert physical.fp == 0 and physical.out_of_frame_finding_ids == ["f.z"]
    assert physical.conditional_fpr.value is None
    assert ratio(0, 0).value is None


def test_informational_cutoff_does_not_change_physical_truth():
    frame = [Opportunity(opportunity_id="norm", track="normative", check_id="schema.id_like_high_cardinality",
        subject="column:measurement", positive=True, severity="INFO", stratum="specificity_challenge",
        matching_check_ids=["schema.id_like_high_cardinality"])]
    info = {"findings": [{"id": "info", "severity": "info", "metadata": {
        "check_id": "schema.id_like_high_cardinality", "subject_key": "column:measurement"}}]}
    assert evaluate_frame(frame, info)[0].tp == 1
    assert evaluate_frame(frame, info, cutoff="LOW")[0].tn == 1


def test_spawn_failure_is_safe_infrastructure(completed, monkeypatch):
    run = completed[0][0]
    spec = RunSpec(**{k: v for k, v in run.model_dump().items() if k in RunSpec.model_fields})
    def unavailable(*args, **kwargs):
        raise OSError("private startup detail")
    monkeypatch.setattr("tadr_benchmark.execution.supervisor.spawn", unavailable)
    observation = invoke_worker(spec, {})
    assert observation.failure_kind == "infrastructure"
    assert observation.original_report is None and observation.runtime_ns is None
    assert observation.instrumentation.monitor_completeness == "no_samples"


def test_result_uses_original_bytes_and_analyze_timer_only(completed, scenario):
    from test_attempt_ledger import monitor
    run = completed[0][0]
    report = completed[1][run.run_id] + b"\n"
    observation = Invocation(report, 2_000_000_000, monitor(run), None, None, None, None, peak_rss_bytes=100)
    names = {*RunSpec.model_fields, *RunResult.__bases__[0].model_fields, "benchmark_git_commit",
             "benchmark_package_version", "logical_dataset_sha256", "source_file_sha256", "environment_id"}
    binding = {k: v for k, v in run.model_dump().items() if k in names}
    result = successful_result(binding, scenario, observation)
    assert result.canonical_report_sha256 == sha256(report)
    assert result.runtime_seconds == 2.0
    assert result.throughput_rows_per_second == 5.0
    with pytest.raises(ValueError):
        successful_result(binding, scenario, replace(observation, runtime_ns=None))


def test_executor_persists_once_and_resumes_without_target_reinvocation(tmp_path, monkeypatch, campaign, scenario, environment, completed):
    from types import SimpleNamespace
    from test_attempt_ledger import monitor
    from tadr_benchmark.execution.executor import execute_run
    from tadr_benchmark.execution.ledger import RunLedger
    run = completed[0][0]
    spec = RunSpec(**{k: getattr(run, k) for k in RunSpec.model_fields})
    original = completed[1][run.run_id]
    monkeypatch.setattr("tadr_benchmark.execution.executor.require_clean_revision", lambda *args: campaign.benchmark_git_commit)
    monkeypatch.setattr("tadr_benchmark.execution.executor.materialize", lambda *args: SimpleNamespace(
        logical_dataset_sha256=run.logical_dataset_sha256, source_file_sha256=run.source_file_sha256,
        relative_path=".work/fixture.csv"))
    calls = []
    def fixture_worker(*args, **kwargs):
        calls.append(args[1])
        return Invocation(original, 2_000_000_000, monitor(run), None, None, None, None, peak_rss_bytes=100)
    monkeypatch.setattr("tadr_benchmark.execution.executor.invoke_worker", fixture_worker)
    with RunLedger(tmp_path / "ledger", [spec], {}) as ledger:
        first = execute_run(tmp_path, campaign, spec, scenario, environment, ledger)
        second = execute_run(tmp_path, campaign, spec, scenario, environment, ledger)
        assert first == second == run
        assert len(calls) == 1 and len(ledger.snapshot()) == 1
        assert (tmp_path / "ledger" / ledger.snapshot()[0].attempt_id / "report.json").read_bytes() == original


def test_auxiliary_typed_decimal_transport_matches_public_numbers_without_coercing_strings():
    from decimal import Decimal
    from tadr_benchmark.execution.diagnostics import report_visible_facts
    facts = {"analysis_stats": {"sample_ratio": Decimal(2)/3}, "dataset_profile": {"columns": [{
        "missing_rate": Decimal("0.123456"), "string_stats": {"avg_len": Decimal("2.23072")},
        "top_values": [{"value": ["string", "0.123456"], "count": 5}]}]}}
    view = report_visible_facts(facts)
    assert view["analysis_stats"]["sample_ratio"] == 0.6667
    column = view["dataset_profile"]["columns"][0]
    assert column["missing_rate"] == 0.1235 and column["string_stats"]["avg_len"] == 2.23072
    assert column["top_values"][0]["value"] == ["string", "0.123456"]
    assert facts["dataset_profile"]["columns"][0]["missing_rate"] == Decimal("0.123456")


def test_diagnostic_binds_original_profile_provenance_and_immutable_cache(completed, tmp_path):
    from tadr_benchmark.execution.diagnostics import diagnostic_record, persist_diagnostic, load_diagnostic, METRICS
    from tadr_benchmark.serialization import canonical_bytes
    primary = completed[0][0]
    report = json.loads(completed[1][primary.run_id])
    report["dataset_profile"] = {"columns": []}
    original = canonical_bytes(report)
    primary = RunResult.model_validate({**primary.model_dump(), "canonical_report_sha256": sha256(original)})
    payload = {"analysis_stats": report["analysis_stats"], "dataset_profile": report["dataset_profile"],
        "algorithm_version": primary.target_algorithm_version, "threshold_profile": primary.target_threshold_profile,
        "protocol_version": primary.target_bundle_protocol,
        "metrics": {k: {"value": None, "unavailable_reason": "not_exposed"} for k in METRICS}}
    diagnostic = diagnostic_record(primary, original, payload)
    path = tmp_path / "companion.json"
    persist_diagnostic(path, diagnostic)
    assert load_diagnostic(path, primary, original) == diagnostic
    with pytest.raises(ValueError, match="provenance"):
        diagnostic_record(primary, original, {**payload, "algorithm_version": "9.0"})
    with pytest.raises(ValueError, match="shared primary"):
        diagnostic_record(primary, original, {**payload, "dataset_profile": {"columns": [{"name": "different"}]}})
    altered = RunResult.model_validate({**primary.model_dump(), "source_file_sha256": "e"*64})
    with pytest.raises(ValueError, match="provenance"):
        load_diagnostic(path, altered, original)
    path.write_bytes(path.read_bytes().replace(b"not_exposed", b"diagnostic_failed", 1))
    with pytest.raises(ValueError, match="checksum"):
        load_diagnostic(path, primary, original)


@pytest.mark.parametrize("kind,category,cap", [("direct_leakage", "leakage", 60),
    ("missing_at_inference", "inference_mismatch", 70), ("invalid_timestamp", None, 50)])
def test_gate_transport_uses_structured_category_and_checks_cap_even_when_nonbinding(kind, category, cap):
    from tadr_benchmark.companions import VariantExpectations
    from tadr_benchmark.evaluation.metrics import evaluate_gates_and_suppression
    labels = VariantExpectations(variant_id="full_reference", findings=[], absent_check_ids=[], gates=[{"kind": kind, "cap": cap}])
    gate = {"type": "hard_gate", "category": category, "value": cap, "reason": "Public explanation of the readiness limit."}
    report = {"findings": [], "readiness_score": 20, "score_breakdown": {"caps_applied": [gate]}}
    assert evaluate_gates_and_suppression(labels, report)["gate_correctness"]["value"] == 1
    gate["value"] = cap+1
    assert evaluate_gates_and_suppression(labels, report)["incorrect_gate_caps"] == [kind]
    report["score_breakdown"]["caps_applied"] = []
    assert evaluate_gates_and_suppression(labels, report)["missing_gates"] == [kind]
    report["score_breakdown"]["caps_applied"] = [gate]
    labels = labels.model_copy(update={"gates": []})
    assert evaluate_gates_and_suppression(labels, report)["false_gates"] == [kind]

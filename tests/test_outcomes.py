import pytest
from pydantic import ValidationError

from tadr_benchmark.campaigns import freeze as publication
from tadr_benchmark.companions import DiagnosticValue, RunFailure
from tadr_benchmark.models import RunResult
from tadr_benchmark.validation import account_outcomes, planned_runs, validate_completed


def failure(run, **changes):
    data = {k: v for k, v in run.model_dump().items() if k in RunFailure.model_fields}
    return RunFailure(**{**data, "failure_kind": "target_input_rejection", "stage": "analyze",
        "error_code": "input_rejected", "exception_class": "InputValidationError",
        "independently_validated_input": True, "adjudication": "valid_target_outcome", **changes})


def test_terminal_target_outcome_counts_without_a_fictional_report(campaign, scenario, completed, environment):
    runs = completed[0]
    failed = failure(runs[0])
    accounting = validate_completed(campaign, [scenario], runs[1:], {environment.environment_id: environment}, [failed])
    assert (accounting.planned, accounting.successful, accounting.adverse_target_outcomes) == (3, 2, 1)
    assert "readiness_score" not in failed.model_dump()
    assert "runtime_seconds" not in failed.model_dump()
    with pytest.raises(ValueError, match="duplicated"):
        account_outcomes(planned_runs(campaign, [scenario]), runs, [failed])


def test_infrastructure_and_pending_adjudication_block_freeze(campaign, scenario, completed, environment):
    for failed in (failure(completed[0][0], adjudication="pending"),
                   failure(completed[0][0], failure_kind="infrastructure", stage="monitor",
                           error_code="instrumentation", exception_class=None,
                           adjudication="infrastructure_failure")):
        with pytest.raises(ValueError):
            validate_completed(campaign, [scenario], completed[0][1:], {environment.environment_id: environment}, [failed])


def test_failure_cannot_disguise_infrastructure_or_raw_diagnostics(completed):
    for changes in ({"independently_validated_input": False}, {"stage": "monitor"},
                    {"failure_kind": "timeout", "error_code": "deadline_exceeded"},
                    {"exception_class": "ArbitraryPrivateException"}, {"message": "raw diagnostic"}):
        with pytest.raises(ValidationError):
            failure(completed[0][0], **changes)


def test_timeout_records_censoring_limit_without_successful_measurement(completed):
    failed = failure(completed[0][0], failure_kind="timeout", error_code="deadline_exceeded",
                     exception_class=None, elapsed_seconds=60.0, policy_limit=60.0)
    assert failed.elapsed_seconds == failed.policy_limit
    assert "peak_rss_bytes" not in failed.model_dump()


def test_all_adverse_outcomes_can_freeze_honestly(campaign, scenario, completed, environment, tmp_path, monkeypatch):
    monkeypatch.setattr(publication, "require_clean_revision", lambda *args: "b"*40)
    monkeypatch.setattr(publication, "repository_issues", lambda *args, **kwargs: [])
    path = publication.freeze(tmp_path, campaign, [scenario], [], {environment.environment_id: environment},
        {}, "2026-01-01", public_reviewed=True, failures=[failure(r) for r in completed[0]])
    _, summary = publication.verify_frozen(path)
    assert summary.groups == []
    assert summary.successful_runs == 0 and summary.adverse_target_outcomes == 3
    assert (path / "runs.jsonl").read_bytes() == b""
    assert not (path / "figures").exists()
    assert "![Runtime]" not in (path / "REPORT.md").read_text()


def test_missed_expected_finding_remains_successful_adverse_observation(completed):
    run = RunResult.model_validate({**completed[0][0].model_dump(),
        "expected_finding_ids_or_patterns": [{"id_pattern": "quality.fixture::*", "subject": "column:x"}],
        "detection_outcome": {"matched_expectations": [], "missed_expectations": [0],
            "violated_absent_expectations": [], "unexpected_finding_ids": [], "gate_expectation_met": True}})
    assert run.detection_outcome.missed_expectations == [0]


def test_diagnostic_missing_value_requires_explicit_reason():
    assert DiagnosticValue(value=None, unavailable_reason="not_exposed").value is None
    for values in ({"value": None, "unavailable_reason": None},
                   {"value": 0.0, "unavailable_reason": "not_exposed"}):
        with pytest.raises(ValidationError):
            DiagnosticValue(**values)

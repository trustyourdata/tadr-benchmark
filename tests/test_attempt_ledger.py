import pytest

from tadr_benchmark.companions import InstrumentationRecord, RunFailure
from tadr_benchmark.execution.attempts import make_attempt, validate_attempts
from tadr_benchmark.execution.ledger import RunLedger
from tadr_benchmark.models import RunSpec
from tadr_benchmark.serialization import canonical_bytes


def interrupted(run):
    return RunFailure(**{k: v for k, v in run.model_dump().items() if k in RunFailure.model_fields},
        failure_kind="infrastructure", stage="startup", error_code="transport",
        independently_validated_input=True, adjudication="infrastructure_failure")


def monitor(run):
    return InstrumentationRecord(run_id=run.run_id, baseline_rss_bytes=20, sample_count=4,
        maximum_sample_gap_seconds=0.01, analysis_start_acknowledged=True, analysis_end_acknowledged=True,
        effective_context_confirmed=True, polars_max_threads=4, terminal_state="success", rss_abort_limit_bytes=2**33)


def specs(runs):
    return [RunSpec(**{k: v for k, v in r.model_dump().items() if k in RunSpec.model_fields}) for r in runs]


@pytest.mark.parametrize("artifact", ["outcome.json", "instrumentation.json"])
def test_resume_rejects_changed_measurements_even_with_unchanged_report(tmp_path, completed, artifact):
    import json
    run, reports = completed[0][0], completed[1]
    with RunLedger(tmp_path, specs([run]), {}) as ledger:
        identity = ledger.begin(interrupted(run))
        ledger.complete(identity, run, monitor(run), reports[run.run_id])
    path = tmp_path / identity / artifact
    data = json.loads(path.read_bytes())
    if artifact == "outcome.json":
        data.update(runtime_seconds=1.0, throughput_rows_per_second=10.0)
    else:
        data["sample_count"] += 1
    path.write_bytes(canonical_bytes(data))
    with pytest.raises(ValueError, match="completion checksum"):
        with RunLedger(tmp_path, specs([run]), {}):
            pass


def test_interruption_requires_resolution_and_resume_preserves_original_bytes(tmp_path, completed):
    runs, reports = completed
    run = runs[0]
    with RunLedger(tmp_path, specs([run]), {"benchmark": run.benchmark_git_commit}) as ledger:
        first = ledger.begin(interrupted(run))
    with RunLedger(tmp_path, specs([run]), {"benchmark": run.benchmark_git_commit}) as ledger:
        with pytest.raises(ValueError, match="resolution"):
            ledger.begin(interrupted(run))
        ledger.resolve(first, "harness_fixed")
        second = ledger.begin(interrupted(run))
        ledger.complete(second, run, monitor(run), reports[run.run_id])
        history = ledger.snapshot()
        assert len(history) == 2
        assert history[1].retry_of_attempt_id == first
        assert history[0].infrastructure_resolution_status == "resolved"
        validate_attempts(specs([run]), history, [run], [])
        assert (tmp_path / second / "report.json").read_bytes() == reports[run.run_id]
    with RunLedger(tmp_path, specs([run]), {"benchmark": run.benchmark_git_commit}) as ledger:
        assert ledger.selected(run.run_id) == run
        with pytest.raises(ValueError, match="rerun"):
            ledger.begin(interrupted(run))
    with pytest.raises(ValueError, match="provenance"):
        with RunLedger(tmp_path, specs([run]), {"benchmark": "a"*40}):
            pass


@pytest.mark.parametrize("kind,code,limit", [("target_input_rejection", "input_rejected", None),
    ("target_analysis_failure", "internal_analysis", None), ("timeout", "deadline_exceeded", 60.0),
    ("resource_abort", "rss_limit", float(2**33))])
def test_adverse_target_outcomes_cannot_retry(tmp_path, completed, kind, code, limit):
    run = completed[0][0]
    outcome = RunFailure.model_validate({**interrupted(run).model_dump(), "failure_kind": kind,
        "stage": "analyze", "error_code": code, "adjudication": "valid_target_outcome", "policy_limit": limit})
    with RunLedger(tmp_path, specs([run]), {}) as ledger:
        identity = ledger.begin(interrupted(run))
        ledger.complete(identity, outcome, monitor(run))
        with pytest.raises(ValueError):
            ledger.resolve(identity, "harness_fixed")
        with pytest.raises(ValueError, match="rerun"):
            ledger.begin(interrupted(run))


def test_freeze_rejects_orphans_unresolved_multiple_or_changed_selected(completed):
    run = completed[0][0]
    valid = make_attempt(run)
    for attempts, outcomes in [([make_attempt(run, 1)], [run]),
                               ([make_attempt(interrupted(run))], []),
                               ([valid, make_attempt(run, 1)], [run]),
                               ([valid], []), ([], [run])]:
        with pytest.raises(ValueError):
            validate_attempts(specs([run]), attempts, outcomes, [])


def test_report_corruption_blocks_resume(tmp_path, completed):
    run, report = completed[0][0], next(iter(completed[1].values()))
    with RunLedger(tmp_path, specs([run]), {}) as ledger:
        identity = ledger.begin(interrupted(run))
        ledger.complete(identity, run, monitor(run), report)
    (tmp_path / identity / "report.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="checksum"):
        with RunLedger(tmp_path, specs([run]), {}):
            pass


def test_attempt_serialization_has_no_raw_error_fields(completed):
    attempt = make_attempt(interrupted(completed[0][0]))
    encoded = canonical_bytes(attempt)
    assert b'"exception_message"' not in encoded
    with pytest.raises(ValueError):
        type(attempt).model_validate({**attempt.model_dump(), "traceback": "unstructured"})

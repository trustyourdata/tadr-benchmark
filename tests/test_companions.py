import pytest

from tadr_benchmark.campaigns import freeze as publication
from tadr_benchmark.campaigns.companions import validate_companions
from tadr_benchmark.companions import (DatasetIdentity, InstrumentationRecord,
                                      ScenarioExpectations)
from tadr_benchmark.serialization import canonical_bytes, sha256


@pytest.fixture
def companions(scenario, completed):
    """Tiny synthetic transport records; no benchmark evidence is produced."""
    label = ScenarioExpectations(scenario_id=scenario.scenario_id, scenario_version="1.0",
        scenario_sha256=sha256(canonical_bytes(scenario)),
        physical={"scenario_id": scenario.scenario_id, "row_count": 10, "column_names": ["x", "z"], "conditions": []},
        normative=[{"variant_id": "full_reference", "findings": [], "absent_check_ids": [], "gates": []}],
        primary_clean_control_eligible=True)
    dataset = DatasetIdentity(scenario_id=scenario.scenario_id, scenario_version="1.0",
        scenario_sha256=label.scenario_sha256, logical_dataset_sha256="d"*64, source_file_sha256="c"*64,
        logical_schema=[{"name": "x", "logical_type": "string"}, {"name": "z", "logical_type": "string"}],
        row_count=10, writer_policy={"representation": "csv"})
    monitors = [InstrumentationRecord(run_id=r.run_id, baseline_rss_bytes=80, sample_count=10,
        maximum_sample_gap_seconds=0.01, analysis_start_acknowledged=True, analysis_end_acknowledged=True,
        effective_context_confirmed=True, polars_max_threads=4, terminal_state="success",
        rss_abort_limit_bytes=8*1024**3) for r in completed[0]]
    return dict(expectations=[label], datasets=[dataset], instrumentation=monitors, diagnostics=[])


def test_typed_companions_freeze_round_trip(campaign, scenario, completed, environment, companions, tmp_path, monkeypatch):
    monkeypatch.setattr(publication, "require_clean_revision", lambda *args: "b"*40)
    monkeypatch.setattr(publication, "repository_issues", lambda *args, **kwargs: [])
    directory = publication.freeze(tmp_path, campaign, [scenario], completed[0],
        {environment.environment_id: environment}, completed[1], "2026-01-01", public_reviewed=True, **companions)
    publication.verify_frozen(directory)
    for name in ("expectations.json", "dataset_manifest.json", "instrumentation.jsonl", "failures.jsonl"):
        assert name in (directory / "checksums.sha256").read_text()


@pytest.mark.parametrize("failure", ["missing_labels", "missing_dataset", "missing_monitor", "duplicate_monitor",
                                     "wrong_dataset_hash", "wrong_spec_hash", "missing_samples", "wrong_context", "wrong_ledger"])
def test_companion_provenance_and_instrumentation_integrity(campaign, scenario, completed, companions, failure):
    if failure == "missing_labels":
        companions["expectations"] = []
    elif failure == "missing_dataset":
        companions["datasets"] = []
    elif failure == "missing_monitor":
        companions["instrumentation"] = companions["instrumentation"][1:]
    elif failure == "duplicate_monitor":
        companions["instrumentation"].append(companions["instrumentation"][0])
    elif failure in {"wrong_dataset_hash", "wrong_spec_hash"}:
        record = companions["datasets"][0]
        field = "source_file_sha256" if failure == "wrong_dataset_hash" else "scenario_sha256"
        companions["datasets"] = [DatasetIdentity.model_validate({**record.model_dump(), field: "a"*64})]
    elif failure == "wrong_ledger":
        record = companions["expectations"][0]
        companions["expectations"] = [ScenarioExpectations.model_validate({**record.model_dump(),
            "physical": {**record.physical.model_dump(), "row_count": 11}})]
    else:
        record = companions["instrumentation"][0]
        change = {"sample_count": 0} if failure == "missing_samples" else {"effective_context_confirmed": False}
        companions["instrumentation"][0] = InstrumentationRecord.model_validate({**record.model_dump(), **change})
    with pytest.raises(ValueError):
        validate_companions(campaign, [scenario], completed[0], [], **companions)

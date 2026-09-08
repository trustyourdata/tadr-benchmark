"""Scheduling regressions use metadata and synthetic observations, never TADR."""

import json
from collections import Counter
from itertools import groupby
from pathlib import Path
from types import SimpleNamespace

import pytest

from tadr_benchmark.campaigns import runner
from tadr_benchmark.campaigns.loader import load_campaign
from tadr_benchmark.campaigns.schedule import execution_schedule
from tadr_benchmark.companions import InstrumentationRecord, RunFailure
from tadr_benchmark.execution import executor
from tadr_benchmark.execution.attempts import attempt_id
from tadr_benchmark.execution.supervisor import Invocation
from tadr_benchmark.models import CampaignManifest, RunResult
from tadr_benchmark.scenarios.families import load_family_scenarios
from tadr_benchmark.serialization import canonical_bytes
from tadr_benchmark.validation import expand_run_plan


@pytest.fixture
def alpha_schedule(monkeypatch, environment):
    root = Path(__file__).parents[1]
    source = load_campaign(root / "campaigns/ALPHA_BENCHMARK_V1.yaml")
    manifest = CampaignManifest.model_validate({**source.model_dump(), "status": "ready",
        "benchmark_git_commit": "b" * 40, "reproducibility_status": "target_unavailable",
        "execution_readiness": {**source.execution_readiness.model_dump(),
                                "host_provisioned": True, "instrumentation_validated": True}})
    scenarios = load_family_scenarios(root)
    plan = expand_run_plan(manifest, scenarios)
    # Synthetic readiness only; no production host check or target is invoked.
    monkeypatch.setattr(runner, "resolve_manifest", lambda *args: manifest)
    monkeypatch.setattr(runner, "capture_environment", lambda: environment.model_copy(
        update={"python_version": manifest.python_version}))
    return manifest, scenarios, plan


def plan_bytes(plan):
    return canonical_bytes([spec.model_dump(mode="json") for spec in plan])


def test_schedule_preserves_canonical_plan_and_is_independent_of_input_order(alpha_schedule):
    manifest, scenarios, plan = alpha_schedule
    original = plan_bytes(plan)
    schedule = execution_schedule(manifest, scenarios, plan)
    assert plan_bytes(plan) == original
    assert [r.run_id for r in plan] == sorted(r.run_id for r in plan)
    assert schedule != plan
    assert Counter(r.run_id for r in schedule) == Counter(r.run_id for r in plan)
    assert len(schedule) == len({r.run_id for r in schedule}) == 578
    assert Counter(r.phase for r in schedule) == {"warmup": 13, "measurement": 565}
    assert all(any(r is original_spec for original_spec in plan) for r in schedule)
    reordered = manifest.model_copy(update={"execution_groups": list(reversed(manifest.execution_groups)),
        "determinism_cases": list(reversed(manifest.determinism_cases))})
    assert execution_schedule(reordered, list(reversed(scenarios)), list(reversed(plan))) == schedule
    with pytest.raises(ValueError, match="duplicate RunSpec"):
        execution_schedule(manifest, scenarios, [*plan, plan[0]])


def test_runner_dispatches_the_complete_alpha_schedule_in_chronological_order(tmp_path, monkeypatch, alpha_schedule):
    manifest, scenarios, plan = alpha_schedule
    dispatched, bindings = [], []

    class NoopLedger:
        def __init__(self, directory, specs, binding):
            bindings.append(plan_bytes(specs))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def snapshot(self):
            return []

    def record_dispatch(root, manifest, spec, *args, **kwargs):
        dispatched.append(spec)

    monkeypatch.setattr(runner, "RunLedger", NoopLedger)
    monkeypatch.setattr(runner, "execute_run", record_dispatch)
    runner.run_campaign(tmp_path, manifest, scenarios)

    assert bindings == [plan_bytes(plan)]  # Ledger persists the canonical plan.
    assert len(dispatched) == len({r.run_id for r in dispatched}) == 578
    assert Counter(r.run_id for r in dispatched) == Counter(r.run_id for r in plan)
    stages = {"correctness": 0, "sampling_reference": 1, "sampling_bounded": 1,
              "determinism_small": 2, "determinism_sampled": 3, "scale_regular": 4, "scale_large": 5}
    assert [stages[r.execution_group_id] for r in dispatched] == (
        [0] * 310 + [1] * 70 + [2] * 120 + [3] * 24 + [4] * 52 + [5] * 2)

    sampling = [r for r in dispatched if stages[r.execution_group_id] == 1]
    deferred = {r.scenario_id for r in plan if r.execution_group_id == "determinism_sampled"}
    pairs = [(sid, list(items)) for sid, items in groupby(sampling, key=lambda r: r.scenario_id)]
    assert len(pairs) == 36 and [sid for sid, _ in pairs] == sorted(sid for sid, _ in pairs)
    for sid, items in pairs:
        assert [r.analysis_variant for r in items] == (
            ["full_reference"] if sid in deferred else ["full_reference", "HEAD_STRIDE_V1"])
    assert sum(r.scenario_id.startswith("sampling.") and r.phase == "measurement"
               and r.repeat_index == 0 and r.determinism_case_id == "standard" for r in dispatched) == 72

    contexts = ["standard", "hash_one", "hash_fortytwo", "timezone_berlin", "decimal_low", "decimal_high"]
    for group in ("determinism_small", "determinism_sampled"):
        for _, items in groupby((r for r in dispatched if r.execution_group_id == group), key=lambda r: r.scenario_id):
            assert [(r.determinism_case_id, r.repeat_index) for r in items] == [
                (context, repeat) for context in contexts for repeat in (0, 1)]

    regular = [(index, r) for index, r in enumerate(dispatched) if r.execution_group_id == "scale_regular"]
    cells = [(cell, list(items)) for cell, items in groupby(regular, key=lambda item: (
        item[1].scenario_id, item[1].analysis_variant, item[1].determinism_case_id))]
    assert len(cells) == len({cell for cell, _ in cells}) == 13
    for _, items in cells:
        positions, runs = zip(*items)
        assert list(positions) == list(range(positions[0], positions[0] + 4))
        assert [(r.phase, r.repeat_index) for r in runs] == [
            ("warmup", 0), ("measurement", 0), ("measurement", 1), ("measurement", 2)]
    large = [r for r in dispatched if r.execution_group_id == "scale_large"]
    assert [(r.phase, r.repeat_index) for r in large] == [("measurement", 0), ("measurement", 1)]
    assert {r.scenario_id for r in large} == {"scale.analytics.n5000000.w20.pqnative"}


def test_resume_keeps_schedule_and_skips_selected_successes_and_failures(tmp_path, monkeypatch, alpha_schedule):
    """Real executor/ledger, six metadata-only cells and a synthetic no-op worker."""
    manifest, scenarios, canonical_plan = alpha_schedule
    regular_id = "scale.analytics.n10000.w20.csv"
    large_id = "scale.analytics.n5000000.w20.pqnative"
    plan = [r for r in canonical_plan if r.scenario_id in {regular_id, large_id}]
    by_id = {s.scenario_id: s for s in scenarios}
    expected = sorted(plan, key=lambda r: (r.scenario_id != regular_id,
                                           r.phase != "warmup", r.repeat_index))
    assert len(expected) == 6
    # The fixture deliberately selects six existing metadata records only. It
    # does not run the campaign, generate their sources or call a real target.
    monkeypatch.setattr(runner, "planned_runs", lambda *args: plan)
    monkeypatch.setattr(executor, "require_clean_revision", lambda *args: manifest.benchmark_git_commit)
    monkeypatch.setattr(executor, "materialize", lambda *args: SimpleNamespace(
        logical_dataset_sha256="d" * 64, source_file_sha256="c" * 64, relative_path=".work/fixture.csv"))
    invoked, visited = [], []

    def noop_worker(spec, *args, **kwargs):
        invoked.append(spec.run_id)
        failed = spec.repeat_index == 0 and spec.phase == "measurement"
        monitor = InstrumentationRecord(run_id=spec.run_id, baseline_rss_bytes=20, sample_count=4,
            maximum_sample_gap_seconds=0.01, analysis_start_acknowledged=True, analysis_end_acknowledged=True,
            effective_context_confirmed=True, polars_max_threads=4, rss_abort_limit_bytes=2**33,
            terminal_state="failure" if failed else "success")
        if failed:
            return Invocation(None, None, monitor, "target_analysis_failure", "analyze",
                              "internal_analysis", "InternalAnalysisError")
        scenario = by_id[spec.scenario_id]
        report = canonical_bytes({"readiness_score": 100, "report_confidence": 100, "total_risk": "0",
            "category_risks": {"quality": "0"}, "findings": [], "score_breakdown": {"caps_applied": []},
            "remediation_plan": [], "analysis_stats": {"row_count": scenario.row_count,
                "col_count": scenario.column_count, "analysis_mode": "full", "sample_ratio": "1"}})
        return Invocation(report, 1_000_000, monitor, None, None, None, None, peak_rss_bytes=100)

    class CheckpointPause(Exception):
        pass

    pause = True

    def checkpoint(root, manifest, spec, *args, **kwargs):
        if pause and len(invoked) == 2:
            raise CheckpointPause()  # Safe boundary before reserving another attempt.
        visited.append(spec.run_id)
        return executor.execute_run(root, manifest, spec, *args, **kwargs)

    monkeypatch.setattr(executor, "invoke_worker", noop_worker)
    monkeypatch.setattr(runner, "execute_run", checkpoint)
    with pytest.raises(CheckpointPause):
        runner.run_campaign(tmp_path, manifest, scenarios)
    assert invoked == [r.run_id for r in expected[:2]]
    directory = tmp_path / ".work/campaigns/alpha_benchmark_v1/ledger"
    binding = (directory / "binding.json").read_bytes()
    assert json.loads(binding)["run_specs"] == [r.model_dump(mode="json") for r in plan]
    retained = {p: p.read_bytes() for p in directory.glob("attempt.*/*")}

    pause = False
    visited.clear()
    outcomes = runner.run_campaign(tmp_path, manifest, scenarios)
    assert visited == [r.run_id for r in expected]  # Same traversal on resume.
    assert invoked == [r.run_id for r in expected]  # Prior success AND failure skipped.
    assert len(outcomes) == 6 and all(a.selected_as_final_outcome for a in outcomes)
    assert {type(a.outcome) for a in outcomes} == {RunResult, RunFailure}
    assert all(a.attempt_index == 0 and a.retry_of_attempt_id is None
               and a.attempt_id == attempt_id(a.run_id, 0) for a in outcomes)
    assert (directory / "binding.json").read_bytes() == binding
    assert all(p.read_bytes() == data for p, data in retained.items())

    visited.clear()
    assert runner.run_campaign(tmp_path, manifest, scenarios) == outcomes
    assert visited == [r.run_id for r in expected]
    assert invoked == [r.run_id for r in expected]  # Fully complete resume invokes nothing.

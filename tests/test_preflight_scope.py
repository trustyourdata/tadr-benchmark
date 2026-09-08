from tadr_benchmark.execution.preflight import CASES
from tadr_benchmark.scenarios.recipe import recipe_from_id


def test_preflight_is_fixed_small_and_distinct_from_research_plan():
    assert len(CASES) == 6 and len({name for name, _, _ in CASES}) == 6
    recipes = [recipe_from_id(reference) for _, reference, _ in CASES]
    assert max(r.row_count for r in recipes) == 300000
    assert sorted((r.row_count, r.width) for r in recipes if r.family == "scale") == [(100000, 20), (100000, 100)]
    paired = [(reference, variant) for _, reference, variant in CASES if reference.startswith("sampling.")]
    assert len(paired) == 2 and paired[0][0] == paired[1][0]
    assert {v for _, v in paired} == {"full_reference", "HEAD_STRIDE_V1"}


def test_preflight_continuation_retains_primary_and_failed_receipt(tmp_path, monkeypatch, environment):
    import json
    from pathlib import Path
    from types import SimpleNamespace
    import pytest
    from test_attempt_ledger import monitor
    from tadr_benchmark.execution import preflight as module
    from tadr_benchmark.campaigns.loader import load_campaign
    from tadr_benchmark.serialization import canonical_bytes
    manifest = load_campaign(Path(__file__).parents[1] / "campaigns" / "ALPHA_BENCHMARK_V1.yaml")
    cases = CASES[2:4]
    monkeypatch.setattr(module, "CASES", cases)
    monkeypatch.setattr(module, "load_campaign", lambda _: manifest)
    monkeypatch.setattr(module, "capture_environment", lambda: environment)
    monkeypatch.setattr(module, "source_snapshot", lambda _: {"fixture_revision": "a"*40})
    monkeypatch.setattr(module, "write_source", lambda recipe, path: path.write_bytes(b"fixture-source"))
    monkeypatch.setattr(module, "logical_schema", lambda _: {"fixture": "string"})
    monkeypatch.setattr(module, "read_source_schema", lambda *args: {"fixture": "string"})
    monkeypatch.setattr(module, "iter_rows", lambda _: [])
    monkeypatch.setattr(module, "read_logical_source", lambda *args: [])
    monkeypatch.setattr(module, "logical_dataset_sha256", lambda *args: "d"*64)
    called = []
    def public_facts(bounded):
        return {"analysis_stats": {"analysis_mode": "sampled" if bounded else "full", "sample_ratio": 0.6667 if bounded else 1.0},
                "dataset_profile": {"columns": []}}
    def invoke(spec, *args, **kwargs):
        called.append(spec.run_id)
        return SimpleNamespace(runtime_ns=1000, peak_rss_bytes=100, failure_kind=None, error_code=None,
            instrumentation=monitor(spec), original_report=canonical_bytes(public_facts(spec.analysis_variant == "HEAD_STRIDE_V1")))
    monkeypatch.setattr(module, "invoke_worker", invoke)
    def diagnostic(request, *args):
        return {**public_facts(request["constraints"].get("max_memory_mb") == 256),
                "algorithm_version": "1.0", "threshold_profile": "MVP_V1", "protocol_version": "1.0"}
    monkeypatch.setattr(module, "request_diagnostic", lambda *args: (_ for _ in ()).throw(ValueError("fixture transport")))
    with pytest.raises(ValueError, match="fixture transport"):
        module.run_preflight(tmp_path)
    directory = tmp_path / ".work/preflight/software_protocol_v1"
    failed_receipt = (directory / "receipt.json").read_bytes()
    original = (directory / "sampling_full_300k.report.json").read_bytes()
    monkeypatch.setattr(module, "request_diagnostic", diagnostic)
    result = module.run_preflight(tmp_path, resume=True)
    assert result["status"] == "passed" and result["primary_invocations"] == 2 and result["auxiliary_invocations"] == 3
    assert called == ["preflight.sampling_full_300k", "preflight.sampling_bounded_300k"]
    assert (directory / "receipt.json").read_bytes() == failed_receipt
    assert (directory / "sampling_full_300k.report.json").read_bytes() == original
    assert json.loads((directory / "receipt.001.json").read_bytes())["parent_receipt_sha256"]
    with pytest.raises(ValueError, match="infrastructure failure"):
        module.run_preflight(tmp_path, resume=True)


def test_planned_alpha_runner_cannot_invoke_target(monkeypatch):
    from pathlib import Path
    import pytest
    from tadr_benchmark.campaigns.loader import load_campaign
    from tadr_benchmark.campaigns.runner import run_campaign
    root = Path(__file__).parents[1]
    manifest = load_campaign(root / "campaigns" / "ALPHA_BENCHMARK_V1.yaml")
    manifest = manifest.model_copy(update={"status": "planned"})
    def forbidden(*args, **kwargs):
        raise AssertionError("PLANNED campaign reached target execution")
    monkeypatch.setattr("tadr_benchmark.campaigns.runner.execute_run", forbidden)
    with pytest.raises(ValueError):
        run_campaign(root, manifest, [])

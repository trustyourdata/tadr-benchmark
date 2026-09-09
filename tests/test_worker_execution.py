"""Isolated software fixtures, never Alpha research observations."""

import json
import time

import psutil
import pytest

from tadr_benchmark.execution.supervisor import invoke_worker
from tadr_benchmark.instrumentation.rss import RssMonitor
from tadr_benchmark.models import InstrumentationPolicy
from tadr_benchmark.validation import planned_runs

FAKE_TARGET = '''
import decimal, json, os, subprocess, sys, time
from pathlib import Path
__version__ = "0.1.0"
assert os.environ["POLARS_MAX_THREADS"] == "4"
assert os.environ["PYTHONHASHSEED"] == "0"
assert decimal.getcontext().prec == 28
time.sleep(0.1)
class TaskIntent:
    @staticmethod
    def model_validate(value): return value
DeploymentConstraints = TaskIntent
class Report:
    def __init__(self, data): self.data = data
    def canonical_bytes(self):
        time.sleep(self.data.get("serialization_delay", 0))
        return b'{"fixture":true,"unchanged": [1,2]} '
def analyze(data, task, constraints):
    settings = json.loads(Path(data).read_text())
    block = bytearray(settings.get("allocation_bytes", 0))
    for i in range(0, len(block), 4096): block[i] = 1
    child = None
    if settings.get("child_bytes"):
        script = "import time; b=bytearray("+str(settings["child_bytes"])+"); time.sleep(60)"
        child = subprocess.Popen([sys.executable, "-c", script])
        Path(data).with_suffix(".child").write_text(str(child.pid))
    if settings.get("error"):
        raise RuntimeError("unsanitized fixture exception")
    time.sleep(settings.get("sleep", 0.2))
    if child and not settings.get("leave_child"):
        child.terminate(); child.wait()
    return Report(settings)
'''


@pytest.fixture
def controlled_worker(tmp_path, campaign, scenario, private_wheel):
    (tmp_path / "tadr.py").write_text(FAKE_TARGET, encoding="utf-8")
    artifact, digest = private_wheel(tmp_path)
    source = tmp_path / "settings.json"
    source.write_text("{}", encoding="utf-8")
    run = planned_runs(campaign, [scenario])[0]
    from tadr_benchmark.models import TargetMetadata
    request = {"source": str(source), "task": {}, "constraints": {},
               "target": {k: getattr(campaign, k) for k in TargetMetadata.model_fields}}
    request["installation_artifact"] = str(artifact)
    request["target"]["target_installation_artifact_sha256"] = digest
    return tmp_path, source, run, request


def test_context_timing_barriers_and_original_bytes(controlled_worker):
    directory, source, run, request = controlled_worker
    source.write_text(json.dumps({"sleep": 0.15, "serialization_delay": 0.6}), encoding="utf-8")
    before = time.perf_counter()
    result = invoke_worker(run, request, cwd=directory)
    elapsed = time.perf_counter()-before
    assert result.failure_kind is None
    assert result.original_report == b'{"fixture":true,"unchanged": [1,2]} '
    assert 0.12 < result.runtime_ns/1e9 < elapsed-0.5
    assert result.instrumentation.startup_ready_seconds >= 0.1
    assert result.instrumentation.effective_context_confirmed
    assert result.instrumentation.analysis_start_acknowledged and result.instrumentation.analysis_end_acknowledged
    assert result.instrumentation.sample_count >= 3
    assert result.instrumentation.maximum_sample_gap_seconds > 0
    assert result.instrumentation.monitor_completeness == "complete"


def test_nonstandard_seed_and_decimal_context_are_applied_before_import(controlled_worker, private_wheel):
    directory, source, run, request = controlled_worker
    case = run.determinism_context.model_copy(update={"case_id": "fixture.context", "python_hash_seed": 42,
        "decimal_precision": 34, "decimal_rounding": "ROUND_DOWN"})
    run = run.model_copy(update={"determinism_case_id": case.case_id, "determinism_context": case})
    (directory / "tadr.py").write_text(FAKE_TARGET.replace('== "0"', '== "42"').replace('prec == 28',
        'prec == 34\nassert decimal.getcontext().rounding == "ROUND_DOWN"'), encoding="utf-8")
    _, request["target"]["target_installation_artifact_sha256"] = private_wheel(directory)
    result = invoke_worker(run, request, cwd=directory)
    assert result.failure_kind is None and result.instrumentation.effective_context == case


def test_worker_and_child_rss_included_and_cleanup(controlled_worker):
    directory, source, run, request = controlled_worker
    source.write_text(json.dumps({"allocation_bytes": 24*1024**2, "child_bytes": 32*1024**2,
                                  "sleep": 0.6, "leave_child": True}), encoding="utf-8")
    result = invoke_worker(run, request, cwd=directory)
    assert result.failure_kind is None
    assert result.peak_rss_bytes >= result.instrumentation.baseline_rss_bytes + 40*1024**2
    child_pid = int(source.with_suffix(".child").read_text())
    assert not psutil.pid_exists(child_pid)
    assert result.instrumentation.incremental_peak_rss_bytes == result.peak_rss_bytes-result.instrumentation.baseline_rss_bytes


def test_timeout_terminates_tree_without_success_fields(controlled_worker):
    directory, source, run, request = controlled_worker
    source.write_text(json.dumps({"child_bytes": 8*1024**2, "sleep": 60}), encoding="utf-8")
    run = run.model_copy(update={"instrumentation_policy": InstrumentationPolicy(timeout_seconds=0.4, memory_sampling_interval_seconds=0.01)})
    result = invoke_worker(run, request, cwd=directory)
    assert result.failure_kind == "timeout"
    assert result.runtime_ns is None and result.original_report is None
    assert result.policy_limit == 0.4
    assert not psutil.pid_exists(int(source.with_suffix(".child").read_text()))


def test_rss_guardian_terminates_controlled_allocation(controlled_worker):
    directory, source, run, request = controlled_worker
    baseline = invoke_worker(run, request, cwd=directory)
    source.write_text(json.dumps({"child_bytes": 64*1024**2, "sleep": 60}), encoding="utf-8")
    threshold = baseline.instrumentation.baseline_rss_bytes+24*1024**2
    result = invoke_worker(run, request, cwd=directory, rss_limit_bytes=threshold)
    assert result.failure_kind == "resource_abort"
    assert result.runtime_ns is None and result.original_report is None
    assert result.policy_limit == threshold
    assert not psutil.pid_exists(int(source.with_suffix(".child").read_text()))


def test_cleanup_failure_is_safe_infrastructure_outcome(controlled_worker, monkeypatch):
    from tadr_benchmark.execution.process_tree import ProcessTree, ProcessCleanupError
    directory, source, run, request = controlled_worker
    original_close = ProcessTree.close
    def failed_verification(tree):
        original_close(tree)
        raise ProcessCleanupError("worker session termination barrier failed")
    monkeypatch.setattr(ProcessTree, "close", failed_verification)
    result = invoke_worker(run, request, cwd=directory)
    assert (result.failure_kind, result.stage, result.error_code) == ("infrastructure", "monitor", "instrumentation")
    assert result.original_report is None and result.runtime_ns is None
    assert result.instrumentation.terminal_state == "failure"
    assert result.exception_class is None


def test_safe_target_failure_never_exposes_message(controlled_worker):
    directory, source, run, request = controlled_worker
    source.write_text('{"error":true}', encoding="utf-8")
    result = invoke_worker(run, request, cwd=directory)
    assert result.failure_kind == "target_analysis_failure"
    assert result.error_code == "unexpected_target_exception"
    assert "unsanitized" not in repr(result)


def test_monitor_excludes_supervisor_and_reports_discovery_failure():
    from types import SimpleNamespace
    class Process:
        pid = 7
        def children(self, recursive): return [SimpleNamespace(pid=8, memory_info=lambda: SimpleNamespace(rss=30))]
        def memory_info(self): return SimpleNamespace(rss=20)
    monitor = RssMonitor(7, process_factory=lambda _: Process())
    assert monitor.sample() == 50
    assert monitor.peak == monitor.baseline == 50
    monitor.root.children = lambda **kwargs: (_ for _ in ()).throw(psutil.AccessDenied())
    assert monitor.sample() is None
    assert monitor.discovery_failed and monitor.incomplete
    assert monitor.successful_samples == 1


def test_vanished_child_is_explicit_and_root_disappearance_is_failure():
    from types import SimpleNamespace
    vanished = lambda: (_ for _ in ()).throw(psutil.NoSuchProcess(8))
    root = SimpleNamespace(pid=7, memory_info=lambda: SimpleNamespace(rss=20),
                           children=lambda **kw: [SimpleNamespace(pid=8, memory_info=vanished)])
    monitor = RssMonitor(7, process_factory=lambda _: root)
    assert monitor.sample() == 20 and monitor.vanished == 1
    root.memory_info = vanished
    assert monitor.sample() is None and monitor.incomplete

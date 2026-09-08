"""Fresh worker barriers, monotonic deadlines and absolute sampled RSS."""

import base64
import json
import queue
import subprocess
import sys
import threading
import time
from dataclasses import dataclass

from ..companions import InstrumentationRecord
from ..instrumentation.rss import RssMonitor
from ..models import RunSpec
from .context import ContextAcknowledgement, worker_environment
from .process_tree import spawn


@dataclass(frozen=True)
class Invocation:
    original_report: bytes | None
    runtime_ns: int | None
    instrumentation: InstrumentationRecord
    failure_kind: str | None
    stage: str | None
    error_code: str | None
    exception_class: str | None
    elapsed_seconds: float | None = None
    policy_limit: float | None = None
    peak_rss_bytes: int | None = None


def invoke_worker(run: RunSpec, request: dict, *, python=sys.executable,
                  worker_module="tadr_benchmark.execution.worker", cwd=None,
                  rss_limit_bytes=8*1024**3, startup_timeout=120.0, transport_timeout=120.0) -> Invocation:
    started = time.perf_counter_ns()
    try:
        process, tree = spawn([str(python), "-m", worker_module], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, env=worker_environment(run.determinism_context), cwd=cwd)
    except (OSError, subprocess.SubprocessError):
        instrument = InstrumentationRecord(run_id=run.run_id, baseline_rss_bytes=None, sample_count=0,
            maximum_sample_gap_seconds=None, analysis_start_acknowledged=False, analysis_end_acknowledged=False,
            effective_context_confirmed=False, polars_max_threads=4, terminal_state="failure",
            rss_abort_limit_bytes=rss_limit_bytes, unavailable_reason="no_samples", monitor_completeness="no_samples",
            requested_interval_seconds=run.instrumentation_policy.memory_sampling_interval_seconds)
        return Invocation(None, None, instrument, "infrastructure", "startup", "transport", None)
    events = queue.Queue()
    def reader():
        try:
            while line := process.stdout.readline(32*1024*1024+1):
                if len(line) > 32*1024*1024:
                    raise ValueError("worker frame too large")
                events.put(json.loads(line))
        except Exception:
            events.put({"event": "invalid_transport"})
        finally:
            events.put({"event": "eof"})
    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    monitor = RssMonitor(process.pid)
    ready_latency, acknowledgement = None, None
    analysis_start, analysis_end = False, False
    original, runtime, failure = None, None, None
    elapsed, limit = None, None
    stage = "startup"
    def send(message):
        process.stdin.write((json.dumps(message, allow_nan=False)+"\n").encode())
        process.stdin.flush()
    try:
        send({**request, "context": run.determinism_context.model_dump(mode="json")})
        event = events.get(timeout=startup_timeout)
        if event.get("event") != "ready":
            raise ValueError("worker not ready")
        acknowledgement = ContextAcknowledgement.model_validate(event["context"])
        if acknowledgement.case != run.determinism_context or not all((acknowledgement.target_not_imported,
                acknowledgement.hash_seed_verified, acknowledgement.timezone_verified, acknowledgement.decimal_verified)):
            raise ValueError("context acknowledgement mismatch")
        ready_latency = (time.perf_counter_ns()-started)/1e9
        stage = "monitor"
        if monitor.sample() is None:
            raise ValueError("baseline monitor failed")
        if monitor.peak >= rss_limit_bytes:
            failure = ("infrastructure", "monitor", "instrumentation", None)
        else:
            send({"command": "analyze"})
            analysis_start = True
            stage = "analyze"
            deadline_start = time.perf_counter_ns()
            while True:
                elapsed = (time.perf_counter_ns()-deadline_start)/1e9
                remaining = run.instrumentation_policy.timeout_seconds-elapsed
                if remaining <= 0:
                    failure = ("timeout", "analyze", "deadline_exceeded", None)
                    limit = run.instrumentation_policy.timeout_seconds
                    break
                try:
                    event = events.get(timeout=min(run.instrumentation_policy.memory_sampling_interval_seconds, remaining))
                except queue.Empty:
                    event = None
                if monitor.sample() is None:
                    failure = ("infrastructure", "monitor", "instrumentation", None)
                    break
                elapsed = (time.perf_counter_ns()-deadline_start)/1e9
                if monitor.peak >= rss_limit_bytes:
                    failure = ("resource_abort", "analyze", "rss_limit", None)
                    limit = float(rss_limit_bytes)
                    break
                if event is None:
                    continue
                if event.get("event") != "analyzed":
                    raise ValueError("unexpected worker event")
                analysis_end = True
                runtime = event["runtime_ns"]
                error_code, exception = event["error_code"], event["exception_class"]
                # This sample was taken after analyzed while worker is held alive.
                send({"command": "sampled"})
                stage = "serialization"
                payload = events.get(timeout=transport_timeout)
                if error_code:
                    if payload.get("event") != "failure" or payload.get("error_code") != error_code:
                        raise ValueError("worker failure transport mismatch")
                    kind = "target_input_rejection" if error_code in {"input_rejected", "dataset_read"} else "target_analysis_failure"
                    failure = (kind, "analyze", error_code, exception)
                else:
                    if payload.get("event") != "report" or type(runtime) is not int or runtime <= 0:
                        raise ValueError("worker success transport mismatch")
                    original = base64.b64decode(payload["canonical_base64"], validate=True)
                send({"command": "release"})
                process.wait(timeout=transport_timeout)
                if process.returncode != 0:
                    raise ValueError("worker exit failed")
                break
    except Exception:
        original, runtime = None, None
        failure = ("infrastructure", stage, "context" if stage == "startup" else
                   "instrumentation" if stage == "monitor" else "transport", None)
    finally:
        try:
            tree.close()
        except Exception:
            original, runtime = None, None
            failure = ("infrastructure", "monitor", "instrumentation", None)
        process.stdin.close()
        thread.join(timeout=2)
        process.stdout.close()
    if failure:
        original, runtime = None, None
    instrument = InstrumentationRecord(run_id=run.run_id, baseline_rss_bytes=monitor.baseline,
        sample_count=monitor.successful_samples, maximum_sample_gap_seconds=monitor.largest_gap,
        analysis_start_acknowledged=analysis_start, analysis_end_acknowledged=analysis_end,
        effective_context_confirmed=acknowledgement is not None, polars_max_threads=4,
        terminal_state="failure" if failure else "success", rss_abort_limit_bytes=rss_limit_bytes,
        requested_interval_seconds=run.instrumentation_policy.memory_sampling_interval_seconds,
        startup_ready_seconds=ready_latency,
        monitor_completeness="incomplete" if monitor.incomplete else "complete" if monitor.successful_samples else "no_samples",
        descendant_discovery_failed=monitor.discovery_failed, vanished_process_count=monitor.vanished,
        unavailable_reason="monitor_failed" if monitor.incomplete else "no_samples" if not monitor.successful_samples else None,
        incremental_peak_rss_bytes=None if monitor.peak is None else max(0, monitor.peak-(monitor.baseline or 0)),
        effective_context=acknowledgement.case if acknowledgement else None,
        timezone_verification_method=acknowledgement.timezone_method if acknowledgement else None)
    return Invocation(original, runtime, instrument, *(failure or (None, None, None, None)), elapsed, limit, monitor.peak)

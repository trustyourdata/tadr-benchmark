"""Line-framed private IPC worker; stdout is reserved for safe protocol events.

The completion barrier precedes canonical serialization so sampled headline RSS
does not include report encoding or persistence. Original canonical bytes are
transported only after the supervisor's final-sample acknowledgement.
"""

import base64
import contextlib
import json
import os
import sys
import time
from pathlib import Path

from ..models import DeterminismCase, TargetMetadata
from .context import apply_context


def safe_exception(error: Exception) -> tuple[str, str | None]:
    known = {"InputValidationError": "input_rejected", "DatasetReadError": "dataset_read",
             "UnsupportedFormatError": "dataset_read", "AnalysisResourceError": "analysis_resource",
             "InternalAnalysisError": "internal_analysis", "ValidationError": "input_rejected"}
    name = type(error).__name__
    return (known[name], name) if name in known else ("unexpected_target_exception", "UnexpectedTargetException")


def prepare_target(request):
    from ..targets.tadr_core import TadrCoreAdapter
    expected = TargetMetadata.model_validate(request["target"])
    artifact = Path(request["installation_artifact"]) if request.get("installation_artifact") else None
    adapter = (TadrCoreAdapter(expected, artifact) if artifact is not None else
               TadrCoreAdapter.from_local_config(expected, Path.cwd()))
    return adapter.prepare(Path(request["source"]), request["task"], request["constraints"])


def serve(prepare=prepare_target) -> int:
    channel = sys.stdout
    def send(event, **fields):
        channel.write(json.dumps({"event": event, **fields}, separators=(",", ":"), allow_nan=False)+"\n")
        channel.flush()
    def command(expected):
        line = sys.stdin.readline()
        if not line or json.loads(line) != {"command": expected}:
            raise ValueError("invalid supervisor barrier")
    stage = "startup"
    try:
        request = json.loads(sys.stdin.readline())
        acknowledgement = apply_context(DeterminismCase.model_validate(request["context"]))
        with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            prepared = prepare(request)
        analyze, source, task, constraints = prepared.public_api.analyze, prepared.dataset_path, prepared.intent, prepared.constraints
        send("ready", context=acknowledgement.model_dump(mode="json"))
        command("analyze")
        stage = "analyze"
        report, error = None, None
        with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            started = time.perf_counter_ns()
            try:
                report = analyze(data=source, task=task, constraints=constraints)
            except Exception as caught:
                error = safe_exception(caught)
            finally:
                ended = time.perf_counter_ns()
        # No report serialization/evaluation happens until final RSS sampling.
        send("analyzed", runtime_ns=None if error else ended-started,
             error_code=None if not error else error[0], exception_class=None if not error else error[1])
        command("sampled")
        stage = "serialization"
        if error:
            send("failure", error_code=error[0], exception_class=error[1], stage="analyze")
        else:
            original = report.canonical_bytes()
            if type(original) is not bytes:
                raise ValueError("canonical report is not bytes")
            send("report", canonical_base64=base64.b64encode(original).decode("ascii"))
        command("release")
        return 0
    except Exception:
        # Never send exception text, traceback, process identifiers or local paths.
        send("infrastructure_failure", stage=stage,
             error_code="context" if stage == "startup" else "transport")
        return 2


if __name__ == "__main__":
    raise SystemExit(serve())

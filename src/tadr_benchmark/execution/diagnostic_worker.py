"""Public-bundle diagnostics in a separate fresh process, never a timed repeat."""

import contextlib
import json
import os
import sys

from ..models import DeterminismCase, TargetMetadata
from .context import apply_context
from .diagnostics import extract_metrics, report_visible_facts
from .worker import prepare_target


def main():
    channel = sys.stdout
    try:
        request = json.loads(sys.stdin.read())
        apply_context(DeterminismCase.model_validate(request["context"]))
        expected = TargetMetadata.model_validate(request["target"])
        with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            prepared = prepare_target(request)
            bundle = prepared.public_api.TADREngine().build_analysis_bundle(
                prepared.dataset_path, prepared.intent, prepared.constraints, include_check_facts=True)
            for field, value in (("algorithm_version", expected.target_algorithm_version),
                                 ("threshold_profile", expected.target_threshold_profile),
                                 ("protocol_version", expected.target_bundle_protocol)):
                if getattr(bundle, field) != value:
                    raise ValueError("observable target provenance mismatch")
            # The full bundle is transient; only these report-visible facts and
            # allowlisted numeric counts leave the worker.
            data = bundle.model_dump(mode="python")
            result = {**report_visible_facts(data), **{k: data[k] for k in (
                "algorithm_version", "threshold_profile", "protocol_version")}}
            result["metrics"] = {k: v.model_dump(mode="json") for k, v in extract_metrics(data, request["case"]).items()}
        channel.write(json.dumps(result, allow_nan=False))
        channel.flush()
        return 0
    except Exception:
        channel.write('{"error_code":"transport"}')
        channel.flush()
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

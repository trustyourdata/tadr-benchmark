"""Separate untimed public-bundle invocation and numeric diagnostic allowlist."""

import json
import subprocess
import sys
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from pathlib import Path

from ..companions import DiagnosticRecord, DiagnosticValue
from ..models import RunResult, TargetMetadata
from ..serialization import sha256, canonical_bytes
from .context import worker_environment
from .process_tree import spawn
from .ledger import write_once

METRICS = ("row_excess", "key_excess", "distinct_count", "nonmissing_count", "class_count", "minority_count",
           "repeated_entity_participants", "complete_pairs", "equality_matches", "mapping_matches",
           "parse_attempts", "parse_failures", "missing_count")


def report_visible_facts(bundle_data: dict) -> dict:
    """Read typed bundle facts at pinned public report precision, leaving strings intact.

    Pydantic JSON mode encodes Decimal as strings; the public canonical report
    encodes numbers and rounds these four typed rate fields to four places.
    This comparison view never modifies or regenerates the primary report.
    """
    rates = {"sample_ratio", "parse_failure_rate", "missing_rate", "empty_rate"}
    def visit(value, key=None):
        if isinstance(value, dict):
            return {k: visit(v, k) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [visit(v) for v in value]
        if isinstance(value, Decimal):
            if not value.is_finite():
                raise ValueError("nonfinite public bundle fact")
            if key in rates:
                with localcontext() as context:
                    context.prec = 50
                    value = value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)
            return int(value) if value == value.to_integral_value() else float(value)
        return value
    return {k: visit(bundle_data[k]) for k in ("analysis_stats", "dataset_profile")}


def extract_metrics(bundle: dict, case: str) -> dict[str, DiagnosticValue]:
    """Read exposed counts only. Absence never produces a reconstructed count."""
    values = {key: DiagnosticValue(value=None, unavailable_reason="not_applicable") for key in METRICS}
    column = "y" if case.startswith("class_") else "probe_id" if case == "cardinality" else "signal_x"
    diagnostics = bundle.get("column_diagnostics", {}).get(column, {})
    duplicate = bundle.get("split_metrics", {}).get("duplicates", {})
    def copy(name, container, key):
        value = container.get(key)
        if value is not None and (type(value) not in {int, float} or value < 0):
            raise ValueError("diagnostic count is not an exposed nonnegative number")
        values[name] = DiagnosticValue(value=None if value is None else float(value),
                                      unavailable_reason="not_exposed" if value is None else None)
    if case in {"missingness", "parse", "cardinality"} or case.startswith("class_"):
        for name, key in (("distinct_count", "observed_distinct"), ("nonmissing_count", "population_nonmissing")):
            copy(name, diagnostics, key)
    if case == "missingness":
        copy("missing_count", diagnostics, "missing_count")
    if case == "parse":
        copy("parse_attempts", diagnostics, "canonical_attempts")
        copy("parse_failures", diagnostics, "canonical_failures")
    if case.startswith("class_"):
        for name in ("class_count", "minority_count"):
            copy(name, diagnostics.get("class_counts", {}), name)
    for expected, name, key in (("duplicate_rows", "row_excess", "row_excess"),
                                ("duplicate_keys", "key_excess", "key_excess"),
                                ("group", "repeated_entity_participants", "repeated_entity_rows")):
        if case == expected:
            copy(name, duplicate, key)
    if case == "leakage":
        pairs = [m for m in bundle.get("relationship_metrics", [])
                 if m.get("check_id") == "leakage.target_direct" and m.get("feature") == "probe_x" and m.get("target") == "y"]
        if len(pairs) > 1:
            raise ValueError("ambiguous diagnostic subject")
        for name, key in (("complete_pairs", "effective_rows"), ("equality_matches", "equal_pairs"),
                          ("mapping_matches", "reciprocal_pairs")):
            copy(name, pairs[0] if pairs else {}, key)
    return values


def diagnostic_record(primary: RunResult, original_report: bytes, payload: dict) -> DiagnosticRecord:
    if sha256(original_report) != primary.canonical_report_sha256:
        raise ValueError("primary report checksum mismatch")
    report = json.loads(original_report)
    for field in ("analysis_stats", "dataset_profile"):
        if payload[field] != report[field]:
            raise ValueError("auxiliary diagnostic differs from shared primary report facts")
    required = {"algorithm_version": primary.target_algorithm_version, "threshold_profile": primary.target_threshold_profile,
                "protocol_version": primary.target_bundle_protocol}
    if any(payload[k] != v for k, v in required.items()):
        raise ValueError("observable public bundle provenance mismatch")
    if set(payload["metrics"]) != set(METRICS):
        raise ValueError("diagnostic metric inventory differs from allowlist")
    fields = {k: getattr(primary, k) for k in DiagnosticRecord.model_fields if hasattr(primary, k)}
    return DiagnosticRecord(**fields, primary_run_id=primary.run_id,
        primary_report_sha256=primary.canonical_report_sha256, shared_profile_sha256=sha256(canonical_bytes(report["dataset_profile"])),
        metrics={k: DiagnosticValue.model_validate(v) for k, v in payload["metrics"].items()})


def persist_diagnostic(path: Path, diagnostic: DiagnosticRecord) -> None:
    data = canonical_bytes(diagnostic)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_once(path, data)
    write_once(path.with_suffix(".sha256"), (sha256(data)+"\n").encode())


def load_diagnostic(path: Path, primary: RunResult, original_report: bytes) -> DiagnosticRecord:
    data = path.read_bytes()
    if path.with_suffix(".sha256").read_text().strip() != sha256(data):
        raise ValueError("cached diagnostic checksum mismatch")
    diagnostic = DiagnosticRecord.model_validate_json(data)
    if sha256(original_report) != primary.canonical_report_sha256 or (
            diagnostic.primary_run_id != primary.run_id or diagnostic.primary_report_sha256 != primary.canonical_report_sha256):
        raise ValueError("cached diagnostic primary report mismatch")
    if any(getattr(diagnostic, k) != getattr(primary, k) for k in DiagnosticRecord.model_fields if hasattr(primary, k)):
        raise ValueError("cached diagnostic provenance mismatch")
    if diagnostic.shared_profile_sha256 != sha256(canonical_bytes(json.loads(original_report)["dataset_profile"])):
        raise ValueError("cached diagnostic shared profile mismatch")
    if set(diagnostic.metrics) != set(METRICS):
        raise ValueError("cached diagnostic metric inventory mismatch")
    return diagnostic


def invoke_diagnostic(primary: RunResult, source: Path, task: dict, case: str, original_report: bytes,
                      *, local_checkout: Path | None = None, python=sys.executable) -> DiagnosticRecord:
    request = {"target": {k: getattr(primary, k) for k in TargetMetadata.model_fields},
        "context": primary.determinism_context.model_dump(mode="json"), "source": str(source), "task": task,
        "constraints": primary.constraints, "case": case,
        "local_checkout": str(local_checkout) if local_checkout else None}
    return diagnostic_record(primary, original_report,
        request_diagnostic(request, primary.determinism_context, primary.instrumentation_policy.timeout_seconds, python=python))


def request_diagnostic(request: dict, context, timeout: float, *, python=sys.executable) -> dict:
    """Private transport shared by research execution and explicit software preflight."""
    process, tree = spawn([str(python), "-m", "tadr_benchmark.execution.diagnostic_worker"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        env=worker_environment(context))
    try:
        data, _ = process.communicate(json.dumps(request).encode(), timeout=timeout)
        if process.returncode != 0 or len(data) > 32*1024*1024:
            raise ValueError("auxiliary diagnostic failed")
        return json.loads(data)
    finally:
        tree.close()
        for stream in (process.stdin, process.stdout):
            if stream is not None:
                stream.close()

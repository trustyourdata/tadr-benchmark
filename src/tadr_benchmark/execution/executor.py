"""Persist selected observations from the isolated public API worker."""

import json
from pathlib import Path

from ..campaigns.freeze import require_clean_revision, validate_reports
from ..companions import RunFailure
from ..evaluation.detection import evaluate
from ..generators.cache import materialize
from ..models import CampaignManifest, EnvironmentInfo, RunResult, RunSpec, ScenarioSpec, TargetMetadata
from ..paths import contained
from ..paths import contained
from ..safety import text_issues, structured_issues
from ..serialization import canonical_bytes, sha256
from ..validation import run_ground_truth
from .ledger import RunLedger
from .supervisor import Invocation, invoke_worker


def successful_result(binding: dict, scenario: ScenarioSpec, observation: Invocation) -> RunResult:
    """Parse an evaluation copy, retaining the original byte string as authority."""
    original = observation.original_report
    if original is None or observation.runtime_ns is None or observation.peak_rss_bytes is None:
        raise ValueError("successful observation requires all measurement fields")
    if text_issues(original.decode("utf-8")):
        raise ValueError("unsafe original report")
    report = json.loads(original)
    if structured_issues(report):
        raise ValueError("unsafe original report fields")
    stats, findings = report["analysis_stats"], report["findings"]
    truth = run_ground_truth(scenario, binding["analysis_variant"])
    ids = [f["id"] for f in findings]
    subjects = [f["metadata"]["subject_key"] for f in findings]
    gates = [cap["reason"] for cap in report["score_breakdown"]["caps_applied"] if cap["type"] == "hard_gate"]
    seconds = observation.runtime_ns/1e9
    result = RunResult(**binding, task_type=scenario.task_type, source_format=scenario.source_format,
        row_count=scenario.row_count, column_count=scenario.column_count,
        analysis_mode=stats["analysis_mode"], sample_ratio=float(stats["sample_ratio"]),
        runtime_seconds=seconds, throughput_rows_per_second=scenario.row_count/seconds,
        peak_rss_bytes=observation.peak_rss_bytes, readiness_score=report["readiness_score"],
        report_confidence=report["report_confidence"], total_risk=float(report["total_risk"]),
        category_risks={k: float(v) for k, v in report["category_risks"].items()}, finding_ids=ids,
        finding_subjects=subjects, finding_severities=[f["severity"] for f in findings], hard_gates=gates,
        remediation_ids=[r["id"] for r in report["remediation_plan"]],
        expected_finding_ids_or_patterns=truth.expected_findings,
        detection_outcome=evaluate(truth, ids, subjects, gates), canonical_report_sha256=sha256(original))
    validate_reports([result], {result.run_id: original})
    return result


def execute_run(root: Path, manifest: CampaignManifest, spec: RunSpec, scenario: ScenarioSpec,
                environment: EnvironmentInfo, ledger: RunLedger, *, installation_artifact: Path | None = None):
    """One authorized ready RunSpec; never expands or retries a campaign implicitly."""
    if manifest.status != "ready" or manifest.benchmark_git_commit is None:
        raise ValueError("research execution requires a resolved ready manifest")
    require_clean_revision(root, manifest.benchmark_git_commit)
    if spec not in ledger.specs or spec.campaign_id != manifest.campaign_id:
        raise ValueError("execution differs from bound ledger plan")
    if (spec.scenario_id != scenario.scenario_id or spec.scenario_version != scenario.scenario_version
            or spec.scenario_sha256 != sha256(canonical_bytes(scenario))):
        raise ValueError("execution scenario differs from RunSpec")
    # Check all bindings even when returning previously completed work.
    dataset = materialize(root, scenario)
    target = {f: getattr(manifest, f) for f in TargetMetadata.model_fields}
    binding = {**target, **spec.model_dump(), "benchmark_git_commit": manifest.benchmark_git_commit,
        "benchmark_package_version": manifest.benchmark_package_version,
        "logical_dataset_sha256": dataset.logical_dataset_sha256,
        "source_file_sha256": dataset.source_file_sha256, "environment_id": environment.environment_id}
    previous = ledger.selected(spec.run_id)
    if previous is not None:
        if any(getattr(previous, k) != v for k, v in binding.items()
               if k not in {"determinism_context", "instrumentation_policy"}):
            raise ValueError("completed work provenance differs from current execution")
        return previous
    reservation = RunFailure(**binding, failure_kind="infrastructure", stage="startup", error_code="transport",
        independently_validated_input=True, adjudication="infrastructure_failure")
    identity = ledger.begin(reservation)
    request = {"target": target, "source": str(contained(root, dataset.relative_path)),
               "task": {"task_type": scenario.task_type, **scenario.task_parameters}, "constraints": spec.constraints}
    if installation_artifact is not None:
        request["installation_artifact"] = str(installation_artifact)
    observation = invoke_worker(spec, request, cwd=root)
    if observation.failure_kind:
        outcome = RunFailure(**binding, failure_kind=observation.failure_kind, stage=observation.stage,
            error_code=observation.error_code, exception_class=observation.exception_class,
            independently_validated_input=True,
            adjudication="infrastructure_failure" if observation.failure_kind == "infrastructure" else "valid_target_outcome",
            elapsed_seconds=observation.elapsed_seconds, policy_limit=observation.policy_limit)
    else:
        try:
            outcome = successful_result(binding, scenario, observation)
        except (ValueError, KeyError, TypeError):
            outcome = RunFailure(**binding, failure_kind="infrastructure", stage="report_validation",
                error_code="transport", independently_validated_input=True, adjudication="infrastructure_failure")
    instrument = observation.instrumentation
    if isinstance(outcome, RunFailure) and instrument.terminal_state != "failure":
        instrument = type(instrument).model_validate({**instrument.model_dump(), "terminal_state": "failure"})
    ledger.complete(identity, outcome, instrument,
                    observation.original_report if isinstance(outcome, RunResult) else None)
    return outcome

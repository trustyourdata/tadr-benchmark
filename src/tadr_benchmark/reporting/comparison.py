from ..models import ComparisonResult, RunResult


def compare(left: RunResult, right: RunResult,
            approved_environment_classes: dict[str, str] | None = None) -> ComparisonResult:
    """Approvals are explicit research inputs, never inferred from OS/CPU labels."""
    dimensions = ("scenario_id", "scenario_version", "scenario_sha256", "logical_dataset_sha256",
                  "benchmark_protocol_version", "result_schema_version", "source_format", "task_type",
                  "row_count", "column_count", "analysis_variant", "constraints", "analysis_mode",
                  "sample_ratio", "phase", "instrumentation_policy", "determinism_context")
    reasons = [f"different {field}" for field in dimensions if getattr(left, field) != getattr(right, field)]
    detection = not reasons and left.phase == "measurement"
    if left.phase != "measurement":
        reasons.append("warmup runs are not comparative measurements")
    classes = approved_environment_classes or {}
    same_class = bool(classes.get(left.environment_id)) and (
        classes.get(left.environment_id) == classes.get(right.environment_id))
    same_bytes = left.source_file_sha256 == right.source_file_sha256
    performance = detection and same_class and same_bytes
    if not same_bytes:
        reasons.append("different source_file_sha256; physical inputs are not byte-identical")
    if not same_class:
        reasons.append("environment classes are not explicitly approved as equivalent")
    a, b = set(left.finding_ids), set(right.finding_ids)
    left_severity = dict(zip(left.finding_ids, left.finding_severities))
    right_severity = dict(zip(right.finding_ids, right.finding_severities))
    common = a & b
    return ComparisonResult(
        left_run_id=left.run_id, right_run_id=right.run_id,
        detection_comparable=detection, performance_comparable=performance, reasons=reasons,
        finding_agreement=(len(a & b) / len(a | b) if a | b else 1.0) if detection else None,
        severity_agreement=sum(left_severity[key] == right_severity[key] for key in common) / len(common)
        if detection and common else None,
        readiness_score_delta=float(right.readiness_score-left.readiness_score) if detection else None,
        report_confidence_delta=float(right.report_confidence-left.report_confidence) if detection else None,
        hard_gates_changed=left.hard_gates != right.hard_gates if detection else None,
        added_finding_ids=sorted(b-a) if detection else [], removed_finding_ids=sorted(a-b) if detection else [],
        runtime_delta_percent=100*(right.runtime_seconds/left.runtime_seconds-1) if performance else None,
        peak_rss_delta_percent=100*(right.peak_rss_bytes/left.peak_rss_bytes-1)
        if performance and left.peak_rss_bytes else None,
        throughput_delta_percent=100*(right.throughput_rows_per_second/left.throughput_rows_per_second-1)
        if performance and left.throughput_rows_per_second else None,
    )


def check_scope_changes(left, right) -> dict[str, list[str]]:
    """Declared support changes, independent of whether a Finding happened to fire."""
    a, b = set(left.planned_scope.check_ids), set(right.planned_scope.check_ids)
    return {"common_checks": sorted(a & b), "newly_supported_checks": sorted(b-a),
            "removed_checks": sorted(a-b)}

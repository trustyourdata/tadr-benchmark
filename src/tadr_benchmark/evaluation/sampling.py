from ..models import RunResult, SamplingComparison, TargetMetadata


def compare_sampling(reference: RunResult, sampled: RunResult, reference_diagnostic=None, sampled_diagnostic=None) -> SamplingComparison:
    dimensions = (*TargetMetadata.model_fields, "scenario_sha256", "logical_dataset_sha256", "source_file_sha256", "scenario_id",
                  "scenario_version", "benchmark_protocol_version", "result_schema_version",
                  "source_format", "task_type", "row_count", "column_count", "determinism_context",
                  "benchmark_git_commit", "benchmark_package_version", "environment_id", "phase", "repeat_index")
    if any(getattr(reference, key) != getattr(sampled, key) for key in dimensions):
        raise ValueError("sampling comparison requires the same dataset, target and semantic protocol")
    if reference.sample_ratio != 1 or reference.analysis_mode == "sampled":
        raise ValueError("sampling reference must analyze the complete dataset")
    if sampled.analysis_mode != "sampled" or sampled.analysis_variant != "HEAD_STRIDE_V1":
        raise ValueError("sampling arm must declare HEAD_STRIDE_V1")
    a_constraints = {k: v for k, v in reference.constraints.items() if k != "max_memory_mb"}
    b_constraints = {k: v for k, v in sampled.constraints.items() if k != "max_memory_mb"}
    if a_constraints != b_constraints:
        raise ValueError("sampling constraints differ beyond the planning budget")
    deltas, unavailable = {}, {}
    if (reference_diagnostic is None) != (sampled_diagnostic is None):
        raise ValueError("primitive comparison requires both diagnostic companions")
    if reference_diagnostic is not None:
        for run, diagnostic in ((reference, reference_diagnostic), (sampled, sampled_diagnostic)):
            if (diagnostic.primary_run_id != run.run_id or diagnostic.primary_report_sha256 != run.canonical_report_sha256
                    or any(getattr(diagnostic, f) != getattr(run, f)
                    for f in ("scenario_sha256", "logical_dataset_sha256", "source_file_sha256", "benchmark_git_commit",
                              "environment_id", "analysis_variant", "determinism_context", "constraints", "analysis_mode",
                              "sample_ratio", *TargetMetadata.model_fields))):
                raise ValueError("diagnostic provenance mismatch")
        if reference_diagnostic.metrics.keys() != sampled_diagnostic.metrics.keys():
            raise ValueError("diagnostic metric inventories differ")
        for name, before in reference_diagnostic.metrics.items():
            after = sampled_diagnostic.metrics[name]
            deltas[name] = None if before.value is None or after.value is None else after.value-before.value
            if deltas[name] is None:
                unavailable[name] = before.unavailable_reason or after.unavailable_reason
    a = dict(zip(reference.finding_ids, reference.finding_severities))
    b = dict(zip(sampled.finding_ids, sampled.finding_severities))
    common, union = a.keys() & b.keys(), a.keys() | b.keys()
    if reference.category_risks.keys() != sampled.category_risks.keys():
        raise ValueError("category sets differ; an explicit schema adapter is required")
    return SamplingComparison(
        reference_run_id=reference.run_id, sampled_run_id=sampled.run_id,
        missed_finding_ids=sorted(a.keys()-b.keys()), added_finding_ids=sorted(b.keys()-a.keys()),
        added_hard_gates=sorted(set(sampled.hard_gates)-set(reference.hard_gates)),
        removed_hard_gates=sorted(set(reference.hard_gates)-set(sampled.hard_gates)),
        primitive_deltas=deltas, primitive_unavailable_reasons=unavailable,
        finding_agreement=len(common) / len(union) if union else 1.0,
        severity_agreement=sum(a[key] == b[key] for key in common) / len(common) if common else None,
        readiness_score_delta=float(sampled.readiness_score-reference.readiness_score),
        report_confidence_delta=float(sampled.report_confidence-reference.report_confidence),
        total_risk_delta=sampled.total_risk-reference.total_risk,
        category_risk_deltas={key: sampled.category_risks[key]-reference.category_risks[key]
                              for key in sorted(reference.category_risks)})

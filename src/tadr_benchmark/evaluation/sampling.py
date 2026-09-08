from ..models import RunResult, SamplingComparison, TargetMetadata


def compare_sampling(reference: RunResult, sampled: RunResult) -> SamplingComparison:
    dimensions = (*TargetMetadata.model_fields, "scenario_sha256", "dataset_sha256", "scenario_id",
                  "scenario_version", "benchmark_protocol_version", "result_schema_version",
                  "source_format", "task_type", "row_count", "column_count", "determinism_context")
    if any(getattr(reference, key) != getattr(sampled, key) for key in dimensions):
        raise ValueError("sampling comparison requires the same dataset, target and semantic protocol")
    if reference.sample_ratio != 1 or reference.analysis_mode == "sampled":
        raise ValueError("sampling reference must analyze the complete dataset")
    if sampled.analysis_mode != "sampled" or sampled.analysis_variant != "HEAD_STRIDE_V1":
        raise ValueError("sampling arm must declare HEAD_STRIDE_V1")
    a = dict(zip(reference.finding_ids, reference.finding_severities))
    b = dict(zip(sampled.finding_ids, sampled.finding_severities))
    common, union = a.keys() & b.keys(), a.keys() | b.keys()
    if reference.category_risks.keys() != sampled.category_risks.keys():
        raise ValueError("category sets differ; an explicit schema adapter is required")
    return SamplingComparison(
        reference_run_id=reference.run_id, sampled_run_id=sampled.run_id,
        finding_agreement=len(common) / len(union) if union else 1.0,
        severity_agreement=sum(a[key] == b[key] for key in common) / len(common) if common else None,
        readiness_score_delta=float(sampled.readiness_score-reference.readiness_score),
        report_confidence_delta=float(sampled.report_confidence-reference.report_confidence),
        total_risk_delta=sampled.total_risk-reference.total_risk,
        category_risk_deltas={key: sampled.category_risks[key]-reference.category_risks[key]
                              for key in sorted(reference.category_risks)})

from collections import defaultdict
from statistics import median

from ..models import CampaignSummary, RunResult, SummaryGroup
from ..companions import RunFailure
from ..serialization import canonical_bytes, sha256


def run_bytes(runs: list[RunResult]) -> bytes:
    if len({run.run_id for run in runs}) != len(runs):
        raise ValueError("duplicate run IDs")
    return b"".join(canonical_bytes(run) for run in sorted(runs, key=lambda item: item.run_id))


def aggregate(campaign_id: str, runs: list[RunResult], failures: list[RunFailure] | None = None,
              attempts=None) -> CampaignSummary:
    failures = failures or []
    groups = defaultdict(list)
    for run in runs:
        if run.campaign_id != campaign_id:
            raise ValueError("mixed campaigns")
        if run.phase == "measurement":
            groups[(run.scenario_id, run.scenario_version, run.analysis_variant, run.environment_id, run.determinism_case_id)].append(run)
    if not groups and not failures:
        raise ValueError("no measured runs to summarize")
    summaries = []
    for (scenario, version, variant, environment, context), members in sorted(groups.items()):
        members.sort(key=lambda r: r.repeat_index)
        scientific = [r for r in members if r.determinism_case_id == "standard" and r.repeat_index == 0
                      and not r.scenario_id.startswith(("scale.", "sampling."))]
        times = [item.runtime_seconds for item in members]
        center = median(times)
        summaries.append(SummaryGroup(
            scenario_id=scenario, scenario_version=version, analysis_variant=variant,
            determinism_case_id=context, runtime_values_seconds=[r.runtime_seconds for r in members],
            peak_rss_values_bytes=[r.peak_rss_bytes for r in members],
            weak_evidence=members[0].row_count == 5000000 and len(members) == 2,
            environment_id=environment, measured_runs=len(members),
            runtime_median_seconds=float(center), runtime_min_seconds=min(times),
            runtime_max_seconds=max(times), runtime_mad_seconds=float(median(abs(t-center) for t in times)),
            throughput_median_rows_per_second=float(median(item.throughput_rows_per_second for item in members)),
            peak_rss_median_bytes=float(median(item.peak_rss_bytes for item in members)),
            readiness_min=min(item.readiness_score for item in members),
            readiness_max=max(item.readiness_score for item in members),
            matched_expectations=sum(len(item.detection_outcome.matched_expectations) for item in scientific),
            missed_expectations=sum(len(item.detection_outcome.missed_expectations) for item in scientific),
            absent_violations=sum(len(item.detection_outcome.violated_absent_expectations) for item in scientific),
            unexpected_findings=sum(len(item.detection_outcome.unexpected_finding_ids) for item in scientific),
            deterministic=len({item.canonical_report_sha256 for item in members}) == 1))
    if any(f.campaign_id != campaign_id or f.adjudication != "valid_target_outcome" for f in failures):
        raise ValueError("summary requires adjudicated adverse target outcomes")
    operational = {}
    if attempts is not None:
        from ..execution.attempts import attempt_bytes, validate_attempts
        from ..models import RunSpec
        specs = {a.run_id: RunSpec(**{k: getattr(a.outcome, k) for k in RunSpec.model_fields}) for a in attempts}
        validate_attempts(list(specs.values()), attempts, runs, failures, complete=False)
        operational = dict(attempts_sha256=sha256(attempt_bytes(attempts)), total_attempts=len(attempts),
            infrastructure_retries=sum(a.attempt_index > 0 for a in attempts),
            resolved_infrastructure_failures=sum(a.infrastructure_resolution_status == "resolved" for a in attempts))
    return CampaignSummary(campaign_id=campaign_id, run_data_sha256=sha256(run_bytes(runs)), groups=summaries,
                           successful_runs=len(runs), adverse_target_outcomes=len(failures),
                           failures_sha256=sha256(run_bytes(failures)), **operational)

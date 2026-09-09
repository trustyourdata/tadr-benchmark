"""Deterministic descriptive table queries over selected authoritative outcomes."""

import csv
import io
import json
from collections import defaultdict
from dataclasses import dataclass, field
from statistics import median

from ..companions import DiagnosticRecord, RunFailure, ScenarioExpectations
from ..evaluation.exact import compare_determinism, compare_formats
from ..evaluation.metrics import (Opportunity, ReportCoverage, aggregate_detection, evaluate_frame,
                                  evaluate_gates_and_suppression, evaluate_scenario, opportunity_coverage, ratio)
from ..evaluation.sampling import compare_sampling
from ..execution.attempts import AttemptRecord, validate_attempts
from ..evaluation.opportunities import alpha_opportunities
from ..models import CampaignManifest, RunResult, ScenarioSpec, TargetMetadata
from ..validation import planned_runs


@dataclass(frozen=True)
class ReportInputs:
    manifest: CampaignManifest
    scenarios: list[ScenarioSpec]
    runs: list[RunResult]
    failures: list[RunFailure]
    reports: dict[str, bytes]
    attempts: list[AttemptRecord]
    expectations: list[ScenarioExpectations] = field(default_factory=list)
    diagnostics: list[DiagnosticRecord] = field(default_factory=list)
    opportunities: dict[tuple[str, str], list[Opportunity]] = field(default_factory=dict)


COVERAGE_RATIOS = ("successful_report_coverage", "positive_successful_report_coverage", "negative_successful_report_coverage")
COVERAGE_COLUMNS = [k for k in ReportCoverage.model_fields if k not in COVERAGE_RATIOS] + [
    key+suffix for key in COVERAGE_RATIOS for suffix in ("_numerator", "_denominator", "")]


def ratio_cells(name, metric):
    return {name+"_numerator": metric.numerator if metric is not None else None,
            name+"_denominator": metric.denominator if metric is not None else None,
            name: metric.value if metric is not None else None}


def coverage_cells(coverage):
    return {**{k: getattr(coverage, k) for k in ReportCoverage.model_fields if k not in COVERAGE_RATIOS},
            **{k: v for name in COVERAGE_RATIOS for k, v in ratio_cells(name, getattr(coverage, name)).items()}}


TABLE_COLUMNS = {
    "identity.csv": ["run_id", "scenario_id", "phase", "repeat_index", "execution_group_id", "analysis_variant",
        "determinism_case_id", "benchmark_git_commit", *TargetMetadata.model_fields, "environment_id",
        "scenario_sha256", "logical_dataset_sha256", "source_file_sha256", "canonical_report_sha256", "terminal_state", "finding_evaluation"],
    "scenario_matrix.csv": ["scenario_id", "scenario_version", "family", "task", "format", "row_count", "column_count",
        "parameters", "physical_conditions", "normative_expectations", "opportunity_frames", "scenario_metrics",
        "challenges", "selected_successes", "selected_failures"],
    "detection_by_check.csv": ["track", "check_id", "stratum", "format", "analysis_variant", "severity_cutoff", "tp", "fp", "fn", "tn",
        "conditional_precision_numerator", "conditional_precision_denominator", "conditional_precision",
        "conditional_recall_numerator", "conditional_recall_denominator", "conditional_recall",
        "conditional_fpr_numerator", "conditional_fpr_denominator", "conditional_fpr", *COVERAGE_COLUMNS,
        "end_to_end_detection_yield_numerator", "end_to_end_detection_yield_denominator", "end_to_end_detection_yield",
        "scenario_detection_numerator", "scenario_detection_denominator",
        "scenario_detection", "all_required_numerator", "all_required_denominator", "all_required", "severity_numerator",
        "severity_denominator", "severity", "detection_severity_numerator", "detection_severity_denominator", "detection_severity",
        "localization_numerator", "localization_denominator", "localization", "out_of_frame_finding_ids", "mapped_detector_details"],
    "clean_false_positives.csv": ["scenario_id", "run_id", "format", "analysis_variant", "track", "stratum",
        "primary_clean_control_eligible", "severity_cutoff", *COVERAGE_COLUMNS,
        "fp", "tn", "conditional_fpr_numerator", "conditional_fpr_denominator", "conditional_fpr",
        "finding_count", "affected_scenario_numerator", "scenario_denominator", "readiness_score", "finding_ids"],
    "threshold_boundaries.csv": ["scenario_id", "run_id", "format", "condition_id", "magnitude", "numerator", "denominator",
        "normative_findings", "observed_findings", "missed_expectations", "absent_violations"],
    "score_sweeps.csv": ["scenario_id", "run_id", "family", "case", "format", "count", "row_count", "readiness_score",
        "report_confidence", "total_risk", "category_risks", "hard_gates"],
    "composite_interactions.csv": ["scenario_id", "run_id", "format", "readiness_score", "findings", "gate_and_suppression_metrics"],
    "remediation.csv": ["scenario_id", "run_id", "order", "remediation_id", "remediation"],
    "determinism.csv": ["scenario_id", "left_run_id", "right_run_id", "left_context", "right_context", "left_repeat", "right_repeat",
        "canonical_bytes_equal", "left_report_sha256", "right_report_sha256", "first_difference_path", "field_agreement"],
    "mismatch_paths.csv": ["comparison_kind", "left_run_id", "right_run_id", "eligible", "first_difference_path", "semantic_first_difference_path"],
    "scale_performance.csv": ["scenario_id", "format", "task", "row_count", "column_count", "analysis_mode", "sample_ratio",
        "measured_successes", "measured_failures", "planned_measurements", "runtime_values_seconds", "runtime_median_seconds",
        "runtime_min_seconds", "runtime_max_seconds", "runtime_mad_seconds", "peak_rss_values_bytes", "peak_rss_median_bytes",
        "peak_rss_min_bytes", "peak_rss_max_bytes", "peak_rss_mad_bytes", "throughput_median_rows_per_second", "weak_evidence"],
    "sampling_fidelity.csv": ["scenario_id", "reference_run_id", "sampled_run_id", "finding_agreement", "severity_agreement",
        "readiness_score_delta", "report_confidence_delta", "total_risk_delta", "category_risk_deltas", "missed_finding_ids",
        "added_finding_ids", "added_hard_gates", "removed_hard_gates"],
    "sampling_primitives.csv": ["scenario_id", "reference_run_id", "sampled_run_id", "metric", "reference_value", "sampled_value",
        "sampled_minus_full", "unavailable_reason", "independent_counts"],
    "format_equivalence.csv": ["scenario_id", "left_run_id", "right_run_id", "comparison_kind", "eligible", "ineligibility_reasons",
        "canonical_bytes_equal", "left_report_sha256", "right_report_sha256", "first_difference_path",
        "semantic_projection_equal", "semantic_first_difference_path", "field_agreement"],
    "failures.csv": ["run_id", "scenario_id", "phase", "analysis_variant", "failure_kind", "stage", "error_code",
        "exception_class", "adjudication", "elapsed_seconds", "policy_limit"],
}


def _cell(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple, bool)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    if isinstance(value, float):
        return repr(value)
    return value


def csv_bytes(columns: list[str], rows: list[dict]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, columns, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    for row in sorted(rows, key=lambda r: tuple(str(_cell(r.get(c))) for c in columns)):
        writer.writerow({c: _cell(row.get(c)) for c in columns})
    return stream.getvalue().encode("utf-8")


def table_rows(inputs: ReportInputs) -> dict[str, list[dict]]:
    from ..campaigns.freeze import validate_reports
    validate_reports(inputs.runs, inputs.reports)
    outcomes = [*inputs.runs, *inputs.failures]
    if len({r.run_id for r in outcomes}) != len(outcomes):
        raise ValueError("table queries require unique selected terminal outcomes")
    plan = planned_runs(inputs.manifest, inputs.scenarios)
    validate_attempts(plan, inputs.attempts,
                      inputs.runs, inputs.failures, complete=False)
    rows = {name: [] for name in TABLE_COLUMNS}
    scenarios = {s.scenario_id: s for s in inputs.scenarios}
    labels = {e.scenario_id: e for e in inputs.expectations}
    reports = {k: json.loads(v) for k, v in inputs.reports.items()}
    diagnostics = {d.primary_run_id: d for d in inputs.diagnostics}
    frames = dict(inputs.opportunities)
    for scenario in inputs.scenarios:
        if scenario.generator == "alpha.tabular":
            from ..scenarios.expectations import expectations_for
            label = labels.get(scenario.scenario_id) or expectations_for(scenario)
            labels[scenario.scenario_id] = label
            for variant in label.normative:
                key = (scenario.scenario_id, variant.variant_id)
                approved = alpha_opportunities(scenario, variant.variant_id, label)
                if key in frames and frames[key] != approved:
                    raise ValueError("supplied opportunity frame differs from approved mapping")
                frames[key] = approved
    standard = [r for r in inputs.runs if r.phase == "measurement" and r.repeat_index == 0 and r.determinism_case_id == "standard"]
    small = [r for r in standard if not r.scenario_id.startswith(("scale.", "sampling."))]
    for outcome in outcomes:
        row = {k: getattr(outcome, k, None) for k in TABLE_COLUMNS["identity.csv"]}
        row["terminal_state"] = "success" if isinstance(outcome, RunResult) else outcome.failure_kind
        row["finding_evaluation"] = "EVALUABLE" if isinstance(outcome, RunResult) else "UNEVALUABLE"
        rows["identity.csv"].append(row)
    for scenario in inputs.scenarios:
        label = labels.get(scenario.scenario_id)
        rows["scenario_matrix.csv"].append(dict(scenario_id=scenario.scenario_id, scenario_version=scenario.scenario_version,
            family=scenario.generator_parameters.get("family"), task=scenario.task_type, format=scenario.source_format,
            row_count=scenario.row_count, column_count=scenario.column_count, parameters=scenario.generator_parameters,
            physical_conditions=label.physical.model_dump(mode="json") if label else None,
            normative_expectations=[v.model_dump(mode="json") for v in label.normative] if label else None,
            opportunity_frames={variant: [o.model_dump(mode="json") for o in frame]
                                for (sid, variant), frame in sorted(frames.items()) if sid == scenario.scenario_id},
            scenario_metrics={}, challenges=[c.model_dump(mode="json") for c in label.challenges] if label else None,
            selected_successes=sum(r.scenario_id == scenario.scenario_id for r in inputs.runs),
            selected_failures=sum(r.scenario_id == scenario.scenario_id for r in inputs.failures)))
    metrics = defaultdict(list)
    selected = {o.run_id: o for o in outcomes}
    scientific_plan = [s for s in plan if s.phase == "measurement" and s.repeat_index == 0
                       and s.determinism_case_id == "standard" and not s.scenario_id.startswith(("scale.", "sampling."))]
    # Start from the declared plan, including cells without a selected report.
    # A failed or pending cell contributes coverage support, never a prediction.
    for spec in scientific_plan:
        scenario = scenarios[spec.scenario_id]
        label = labels.get(spec.scenario_id)
        frame = frames.get((spec.scenario_id, spec.analysis_variant), [])
        if inputs.manifest.campaign_id == "ALPHA_BENCHMARK_V1" and not frame:
            raise ValueError("Alpha detection queries require approved fixed opportunity frames")
        outcome, report = selected.get(spec.run_id), reports.get(spec.run_id)
        failure_kind = outcome.failure_kind if isinstance(outcome, RunFailure) else None
        for cutoff in ("INFO", "LOW"):
            evaluated = evaluate_frame(frame, report, cutoff=cutoff, failure_kind=failure_kind)
            for item in evaluated:
                metrics[(item.track, item.check_id, item.stratum, scenario.source_format, spec.analysis_variant, cutoff)].append(item)
            if label and (label.primary_clean_control_eligible or any(c.interpretation == "specificity" for c in label.challenges)):
                for track in ("normative", "controlled_condition"):
                    coverage = opportunity_coverage([o for o in frame if o.track == track], report, cutoff=cutoff, failure_kind=failure_kind)
                    findings = [f for f in report["findings"] if cutoff == "INFO" or f["severity"].upper() != "INFO"] if report is not None else None
                    fp = sum(m.fp for m in evaluated if m.track == track)
                    tn = sum(m.tn for m in evaluated if m.track == track)
                    rows["clean_false_positives.csv"].append(dict(scenario_id=spec.scenario_id, run_id=spec.run_id,
                        format=scenario.source_format, analysis_variant=spec.analysis_variant, track=track,
                        stratum="primary_clean" if label.primary_clean_control_eligible else "specificity_challenge",
                        primary_clean_control_eligible=label.primary_clean_control_eligible, severity_cutoff=cutoff,
                        **coverage_cells(coverage), fp=fp, tn=tn, **ratio_cells("conditional_fpr", ratio(fp, fp+tn)),
                        finding_count=len(findings) if findings is not None else None,
                        affected_scenario_numerator=int(bool(findings)) if findings is not None else None,
                        scenario_denominator=int(report is not None), readiness_score=outcome.readiness_score if report is not None else None,
                        finding_ids=[f["id"] for f in findings] if findings is not None else None))
        if label:
            normative = next(v for v in label.normative if v.variant_id == spec.analysis_variant)
            matrix = next(row for row in rows["scenario_matrix.csv"] if row["scenario_id"] == spec.scenario_id)
            matrix["scenario_metrics"][spec.analysis_variant] = evaluate_scenario(frame, normative, report, failure_kind=failure_kind)
    for run in small:
        scenario, report = scenarios[run.scenario_id], reports[run.run_id]
        label = labels.get(run.scenario_id)
        if label:
            normative = next(v for v in label.normative if v.variant_id == run.analysis_variant)
            for condition in label.physical.conditions:
                for name, count in condition.counts.items():
                    rows["threshold_boundaries.csv"].append(dict(scenario_id=run.scenario_id, run_id=run.run_id,
                        format=run.source_format, condition_id=condition.condition_id, magnitude=name,
                        numerator=count.numerator, denominator=count.denominator,
                        normative_findings=[f.model_dump(mode="json") for f in normative.findings], observed_findings=report["findings"],
                        missed_expectations=run.detection_outcome.missed_expectations, absent_violations=run.detection_outcome.violated_absent_expectations))
            if scenario.generator_parameters.get("family") == "composite":
                rows["composite_interactions.csv"].append(dict(scenario_id=run.scenario_id, run_id=run.run_id,
                    format=run.source_format, readiness_score=run.readiness_score, findings=report["findings"],
                    gate_and_suppression_metrics=evaluate_gates_and_suppression(normative, report)))
        family = scenario.generator_parameters.get("family")
        if family in {"missing", "duplicate", "class", "leak"}:
            rows["score_sweeps.csv"].append(dict(scenario_id=run.scenario_id, run_id=run.run_id, family=family,
                case=scenario.generator_parameters["case"], format=run.source_format, count=scenario.generator_parameters.get("count"),
                row_count=run.row_count, readiness_score=run.readiness_score, report_confidence=run.report_confidence,
                total_risk=run.total_risk, category_risks=run.category_risks, hard_gates=run.hard_gates))
        for i, remediation in enumerate(report["remediation_plan"]):
            rows["remediation.csv"].append(dict(scenario_id=run.scenario_id, run_id=run.run_id, order=i,
                remediation_id=remediation["id"], remediation=remediation))
    metric_names = {"conditional_precision": "conditional_precision", "conditional_recall": "conditional_recall", "conditional_fpr": "conditional_fpr",
        "scenario_detection": "scenario_detection", "all_required_detected": "all_required",
        "severity_correctness": "severity", "detection_and_severity": "detection_severity", "localization": "localization"}
    for (track, check, stratum, fmt, variant, cutoff), members in sorted(metrics.items()):
        combined = aggregate_detection(members)
        row = dict(track=track, check_id=check, stratum=stratum, format=fmt, analysis_variant=variant, severity_cutoff=cutoff,
                   **coverage_cells(combined), **{k: getattr(combined, k) for k in ("tp", "fp", "fn", "tn")},
                   **ratio_cells("end_to_end_detection_yield", combined.end_to_end_detection_yield))
        for name, prefix in metric_names.items():
            row.update(ratio_cells(prefix, getattr(combined, name)))
        row.update(out_of_frame_finding_ids=combined.out_of_frame_finding_ids, mapped_detector_details=combined.mapped_detector_details)
        rows["detection_by_check.csv"].append(row)
    by_cell = defaultdict(list)
    for run in inputs.runs:
        if run.phase == "measurement":
            by_cell[(run.scenario_id, run.analysis_variant)].append(run)
    for (sid, variant), members in sorted(by_cell.items()):
        members.sort(key=lambda r: (r.determinism_case_id != "standard", r.determinism_case_id, r.repeat_index))
        left = members[0]
        for right in members[1:]:
            comparison = compare_determinism(left, right, inputs.reports)
            rows["determinism.csv"].append(dict(scenario_id=sid, left_run_id=left.run_id, right_run_id=right.run_id,
                left_context=left.determinism_case_id, right_context=right.determinism_case_id,
                left_repeat=left.repeat_index, right_repeat=right.repeat_index,
                **{k: getattr(comparison, k) for k in ("canonical_bytes_equal", "left_report_sha256", "right_report_sha256",
                                                     "first_difference_path", "field_agreement")}))
            if not comparison.canonical_bytes_equal:
                rows["mismatch_paths.csv"].append({k: getattr(comparison, k) for k in TABLE_COLUMNS["mismatch_paths.csv"]})
    for scenario in inputs.scenarios:
        if scenario.generator_parameters.get("family") != "scale":
            continue
        measured = sorted((r for r in inputs.runs if r.scenario_id == scenario.scenario_id and r.phase == "measurement"
                           and r.determinism_case_id == "standard"), key=lambda r: r.repeat_index)
        failed = [f for f in inputs.failures if f.scenario_id == scenario.scenario_id and f.phase == "measurement"]
        times, rss = [r.runtime_seconds for r in measured], [r.peak_rss_bytes for r in measured]
        row = dict(scenario_id=scenario.scenario_id, format=scenario.source_format, task=scenario.task_type,
            row_count=scenario.row_count, column_count=scenario.column_count, measured_successes=len(measured),
            measured_failures=len(failed), planned_measurements=len(measured)+len(failed),
            analysis_mode=measured[0].analysis_mode if measured else None, sample_ratio=measured[0].sample_ratio if measured else None,
            runtime_values_seconds=times, peak_rss_values_bytes=rss, weak_evidence=scenario.row_count == 5000000,
            throughput_median_rows_per_second=median(r.throughput_rows_per_second for r in measured) if measured else None)
        for values, prefix, unit in ((times, "runtime", "seconds"), (rss, "peak_rss", "bytes")):
            for name, value in (("median", median(values) if values else None), ("min", min(values) if values else None),
                                ("max", max(values) if values else None),
                                ("mad", median(abs(v-median(values)) for v in values) if values else None)):
                row[f"{prefix}_{name}_{unit}"] = value
        rows["scale_performance.csv"].append(row)
    standard_map = {(r.scenario_id, r.analysis_variant): r for r in standard}
    for reference in standard:
        if reference.scenario_id.startswith("sampling.") and reference.analysis_variant == "full_reference":
            sampled = standard_map.get((reference.scenario_id, "HEAD_STRIDE_V1"))
            if sampled is None:
                continue  # Its terminal failure remains in failures and coverage.
            before, after = diagnostics.get(reference.run_id), diagnostics.get(sampled.run_id)
            comparison = compare_sampling(reference, sampled, before, after)
            rows["sampling_fidelity.csv"].append({"scenario_id": reference.scenario_id,
                **{k: getattr(comparison, k) for k in TABLE_COLUMNS["sampling_fidelity.csv"] if k != "scenario_id"}})
            if before is not None:
                for metric in before.metrics:
                    rows["sampling_primitives.csv"].append(dict(scenario_id=reference.scenario_id,
                        reference_run_id=reference.run_id, sampled_run_id=sampled.run_id, metric=metric,
                        reference_value=before.metrics[metric].value, sampled_value=after.metrics[metric].value,
                        sampled_minus_full=comparison.primitive_deltas[metric],
                        unavailable_reason=comparison.primitive_unavailable_reasons.get(metric),
                        independent_counts={c.condition_id: {k: v.model_dump() for k, v in c.counts.items()}
                                            for c in labels[reference.scenario_id].physical.conditions}))
        if not reference.scenario_id.endswith(".csv") or scenarios[reference.scenario_id].generator != "alpha.tabular":
            continue
        for suffix in ("pqstr", "pqnative"):
            other_id = reference.scenario_id.removesuffix("csv") + suffix
            other = standard_map.get((other_id, reference.analysis_variant))
            if other is None:
                continue
            comparison = compare_formats(reference, other, scenarios[reference.scenario_id], scenarios[other_id], inputs.reports)
            rows["format_equivalence.csv"].append({"scenario_id": reference.scenario_id,
                **{k: getattr(comparison, k) for k in TABLE_COLUMNS["format_equivalence.csv"] if k != "scenario_id"}})
            if not comparison.canonical_bytes_equal:
                rows["mismatch_paths.csv"].append({k: getattr(comparison, k) for k in TABLE_COLUMNS["mismatch_paths.csv"]})
    for failure in inputs.failures:
        rows["failures.csv"].append({k: getattr(failure, k) for k in TABLE_COLUMNS["failures.csv"]})
    return rows


def build_tables(inputs: ReportInputs) -> dict[str, bytes]:
    return {name: csv_bytes(TABLE_COLUMNS[name], rows) for name, rows in table_rows(inputs).items()}

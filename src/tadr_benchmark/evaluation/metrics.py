"""Fixed-frame descriptive metrics; no opportunities are invented from output."""

from typing import Literal

from pydantic import Field, model_validator

from ..companions import VariantExpectations
from ..models import Contract, Identifier, NonnegativeInt, Rate

SEVERITIES = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
TargetFailureCategory = Literal["target_input_rejection", "target_analysis_failure", "timeout", "resource_abort"]
TARGET_FAILURE_CATEGORIES = ("target_input_rejection", "target_analysis_failure", "timeout", "resource_abort")


class Metric(Contract):
    numerator: NonnegativeInt
    denominator: NonnegativeInt
    value: Rate | None

    @model_validator(mode="after")
    def correct_ratio(self):
        if self.numerator > self.denominator or self.value != (
                self.numerator/self.denominator if self.denominator else None):
            raise ValueError("metric must retain its exact numerator and denominator")
        return self


def ratio(numerator: int, denominator: int) -> Metric:
    return Metric(numerator=numerator, denominator=denominator,
                  value=numerator/denominator if denominator else None)


class Opportunity(Contract):
    opportunity_id: Identifier
    scenario_id: Identifier | None = None
    physical_defect_id: Identifier | None = None
    track: Literal["normative", "controlled_condition"]
    check_id: Identifier
    subject: str
    positive: bool
    severity: Literal["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"] | None = None
    stratum: Identifier
    # A physical condition can explicitly name several observable warning checks;
    # such a frame still contains one condition opportunity, never one per output.
    matching_check_ids: list[Identifier] = Field(min_length=1)


class ReportCoverage(Contract):
    finding_evaluation: Literal["EVALUABLE", "PARTIALLY_EVALUABLE", "UNEVALUABLE"]
    planned_opportunities: NonnegativeInt
    evaluable_opportunities: NonnegativeInt
    unevaluable_opportunities: NonnegativeInt
    planned_positive_opportunities: NonnegativeInt
    evaluable_positive_opportunities: NonnegativeInt
    unevaluable_positive_opportunities: NonnegativeInt
    planned_negative_opportunities: NonnegativeInt
    evaluable_negative_opportunities: NonnegativeInt
    unevaluable_negative_opportunities: NonnegativeInt
    planned_reports: NonnegativeInt
    successful_reports: NonnegativeInt
    terminal_target_failures: NonnegativeInt
    terminal_target_failures_by_category: dict[TargetFailureCategory, NonnegativeInt]
    pending_reports: NonnegativeInt
    successful_report_coverage: Metric
    positive_successful_report_coverage: Metric
    negative_successful_report_coverage: Metric

    @model_validator(mode="after")
    def consistent_coverage(self):
        for prefix in ("", "positive_", "negative_"):
            planned, evaluable, unevaluable = (getattr(self, f"{kind}_{prefix}opportunities")
                                                for kind in ("planned", "evaluable", "unevaluable"))
            coverage = getattr(self, prefix+"successful_report_coverage")
            if planned != evaluable+unevaluable or coverage != ratio(evaluable, planned):
                raise ValueError("coverage must retain planned, evaluable and unevaluable opportunity support")
        for kind in ("planned", "evaluable", "unevaluable"):
            if getattr(self, kind+"_opportunities") != sum(getattr(self, kind+"_"+c+"_opportunities") for c in ("positive", "negative")):
                raise ValueError("positive/negative opportunity support differs")
        if (set(self.terminal_target_failures_by_category) != set(TARGET_FAILURE_CATEGORIES)
                or self.terminal_target_failures != sum(self.terminal_target_failures_by_category.values())
                or self.planned_reports != self.successful_reports+self.terminal_target_failures+self.pending_reports):
            raise ValueError("report availability must retain separate terminal categories and pending reports")
        if ((not self.successful_reports and self.evaluable_opportunities)
                or (self.successful_reports == self.planned_reports and self.unevaluable_opportunities)
                or (not self.planned_reports and self.planned_opportunities)):
            raise ValueError("opportunity evaluability requires matching planned report availability")
        status = "UNEVALUABLE" if not self.successful_reports else (
            "EVALUABLE" if self.successful_reports == self.planned_reports else "PARTIALLY_EVALUABLE")
        if self.finding_evaluation != status:
            raise ValueError("Finding evaluability differs from report availability")
        return self


def report_coverage(planned_positive: int, planned_negative: int, evaluable_positive: int,
                    evaluable_negative: int, *, successful_reports: int, failures: dict[str, int], pending_reports=0) -> ReportCoverage:
    if set(failures)-set(TARGET_FAILURE_CATEGORIES):
        raise ValueError("infrastructure history is separate from selected target failures")
    failures = {k: failures.get(k, 0) for k in TARGET_FAILURE_CATEGORIES}
    failed = sum(failures.values())
    planned_reports = successful_reports+failed+pending_reports
    fields = {}
    for prefix, planned, evaluable in (("", planned_positive+planned_negative, evaluable_positive+evaluable_negative),
            ("positive_", planned_positive, evaluable_positive), ("negative_", planned_negative, evaluable_negative)):
        fields.update({"planned_"+prefix+"opportunities": planned, "evaluable_"+prefix+"opportunities": evaluable,
                       "unevaluable_"+prefix+"opportunities": planned-evaluable,
                       prefix+"successful_report_coverage": ratio(evaluable, planned)})
    return ReportCoverage(**fields, planned_reports=planned_reports, successful_reports=successful_reports,
        terminal_target_failures=failed, terminal_target_failures_by_category=failures, pending_reports=pending_reports,
        finding_evaluation="UNEVALUABLE" if not successful_reports else "EVALUABLE" if successful_reports == planned_reports else "PARTIALLY_EVALUABLE")


def positive_at_cutoff(opportunity: Opportunity, cutoff: str) -> bool:
    if cutoff not in {"INFO", "LOW"}:
        raise ValueError("unregistered severity cutoff")
    return opportunity.positive and not (opportunity.track == "normative" and opportunity.severity is not None
                                         and SEVERITIES[opportunity.severity] < SEVERITIES[cutoff])


def opportunity_coverage(opportunities: list[Opportunity], report: dict | None, *, cutoff="INFO", failure_kind=None) -> ReportCoverage:
    if failure_kind is not None and (failure_kind not in TARGET_FAILURE_CATEGORIES or report is not None):
        raise ValueError("coverage accepts selected target failures without reports, never infrastructure attempts")
    positive = sum(positive_at_cutoff(o, cutoff) for o in opportunities)
    negative = len(opportunities)-positive
    present = report is not None
    return report_coverage(positive, negative, positive if present else 0, negative if present else 0,
        successful_reports=int(present), failures={failure_kind: 1} if failure_kind else {},
        pending_reports=int(not present and failure_kind is None))


class DetectionMetrics(ReportCoverage):
    track: Literal["normative", "controlled_condition"]
    check_id: Identifier
    stratum: Identifier
    severity_cutoff: Literal["INFO", "LOW"]
    tp: NonnegativeInt
    fp: NonnegativeInt
    fn: NonnegativeInt
    tn: NonnegativeInt
    conditional_precision: Metric
    conditional_recall: Metric
    conditional_fpr: Metric
    end_to_end_detection_yield: Metric | None
    scenario_detection: Metric
    all_required_detected: Metric
    severity_correctness: Metric
    detection_and_severity: Metric
    localization: Metric
    out_of_frame_finding_ids: list[str]
    mapped_detector_details: dict[str, list[str]] = {}

    @model_validator(mode="after")
    def consistent_detection(self):
        if (self.tp+self.fn != self.evaluable_positive_opportunities or self.fp+self.tn != self.evaluable_negative_opportunities
                or self.conditional_precision != ratio(self.tp, self.tp+self.fp)
                or self.conditional_recall != ratio(self.tp, self.tp+self.fn)
                or self.conditional_fpr != ratio(self.fp, self.fp+self.tn)):
            raise ValueError("conditional Finding counts require evaluable report opportunities")
        expected_yield = ratio(self.tp, self.planned_positive_opportunities) if self.track == "controlled_condition" else None
        if self.end_to_end_detection_yield != expected_yield:
            raise ValueError("end-to-end detection yield uses all planned positive physical opportunities")
        return self


def evaluate_frame(opportunities: list[Opportunity], report: dict | None, *, cutoff="INFO", failure_kind=None) -> list[DetectionMetrics]:
    if cutoff not in {"INFO", "LOW"}:
        raise ValueError("unregistered severity cutoff")
    if len({o.opportunity_id for o in opportunities}) != len(opportunities):
        raise ValueError("duplicate opportunity identity")
    physical = [(o.scenario_id, o.physical_defect_id, o.subject) for o in opportunities
                if o.track == "controlled_condition" and o.physical_defect_id is not None]
    if len(physical) != len(set(physical)):
        raise ValueError("duplicate physical condition opportunity")
    findings = [f for f in report["findings"] if SEVERITIES[f["severity"].upper()] >= SEVERITIES[cutoff]] if report is not None else []
    groups = sorted({(o.track, o.check_id, o.stratum) for o in opportunities})
    result = []
    for track, check, stratum in groups:
        frame = [o for o in opportunities if (o.track, o.check_id, o.stratum) == (track, check, stratum)]
        coverage = opportunity_coverage(frame, report, cutoff=cutoff, failure_kind=failure_kind)
        relevant_checks = {c for o in frame for c in o.matching_check_ids}
        relevant = [f for f in findings if f["metadata"]["check_id"] in relevant_checks]
        tp = fp = fn = tn = correct = severity_matched = severity_positive = localized = 0
        positives = 0
        detector_details = {}
        # No report is UNEVALUABLE, never an empty/negative prediction.
        for opportunity in frame if report is not None else []:
            matches = [f for f in relevant if f["metadata"]["check_id"] in opportunity.matching_check_ids
                       and f["metadata"]["subject_key"] == opportunity.subject]
            detector_details[opportunity.opportunity_id] = sorted({f["metadata"]["check_id"] for f in matches})
            # INFO-only normative expectations become negatives at the actionable
            # cutoff; physical presence is independent of warning severity.
            positive = positive_at_cutoff(opportunity, cutoff)
            positives += positive
            tp += bool(positive and matches)
            fn += bool(positive and not matches)
            fp += bool(not positive and matches)
            tn += bool(not positive and not matches)
            if positive:
                localized += len(matches)
                if opportunity.severity is not None:
                    severity_positive += 1
                    severity_matched += bool(matches)
                    correct += bool(matches) and all(f["severity"].upper() == opportunity.severity for f in matches)
        out_of_frame = [f["id"] for f in relevant if not any(
            f["metadata"]["check_id"] in o.matching_check_ids and f["metadata"]["subject_key"] == o.subject for o in frame)]
        expected_families = {c for o in frame if o.positive for c in o.matching_check_ids}
        detections_of_expected_family = sum(f["metadata"]["check_id"] in expected_families for f in relevant)
        result.append(DetectionMetrics(**coverage.model_dump(), track=track, check_id=check, stratum=stratum, severity_cutoff=cutoff,
            tp=tp, fp=fp, fn=fn, tn=tn, conditional_precision=ratio(tp, tp+fp), conditional_recall=ratio(tp, tp+fn),
            conditional_fpr=ratio(fp, fp+tn),
            end_to_end_detection_yield=ratio(tp, coverage.planned_positive_opportunities) if track == "controlled_condition" else None,
            scenario_detection=ratio(int(tp > 0), int(positives > 0)),
            all_required_detected=ratio(int(positives > 0 and fn == 0), int(positives > 0)),
            severity_correctness=ratio(correct, severity_matched), detection_and_severity=ratio(correct, severity_positive),
            localization=ratio(localized, detections_of_expected_family), out_of_frame_finding_ids=sorted(out_of_frame),
            mapped_detector_details=detector_details))
    return result


def aggregate_detection(members: list[DetectionMetrics]) -> DetectionMetrics:
    if not members or len({(m.track, m.check_id, m.stratum, m.severity_cutoff) for m in members}) != 1:
        raise ValueError("detection aggregation requires a common declared frame group")
    first = members[0]
    total = lambda key: sum(getattr(m, key) for m in members)
    coverage = report_coverage(*(total(k) for k in ("planned_positive_opportunities", "planned_negative_opportunities",
        "evaluable_positive_opportunities", "evaluable_negative_opportunities")), successful_reports=total("successful_reports"),
        failures={k: sum(m.terminal_target_failures_by_category[k] for m in members) for k in TARGET_FAILURE_CATEGORIES},
        pending_reports=total("pending_reports"))
    metrics = {name: ratio(sum(getattr(m, name).numerator for m in members), sum(getattr(m, name).denominator for m in members))
        for name in ("conditional_precision", "conditional_recall", "conditional_fpr", "scenario_detection", "all_required_detected",
                     "severity_correctness", "detection_and_severity", "localization")}
    return DetectionMetrics(**coverage.model_dump(), **metrics, track=first.track, check_id=first.check_id, stratum=first.stratum,
        severity_cutoff=first.severity_cutoff, **{k: total(k) for k in ("tp", "fp", "fn", "tn")},
        end_to_end_detection_yield=ratio(total("tp"), coverage.planned_positive_opportunities) if first.track == "controlled_condition" else None,
        out_of_frame_finding_ids=sorted(f for m in members for f in m.out_of_frame_finding_ids),
        mapped_detector_details={k: v for m in members for k, v in m.mapped_detector_details.items()})


def evaluate_gates_and_suppression(labels: VariantExpectations, report: dict) -> dict:
    caps = report["score_breakdown"]["caps_applied"]
    expected = {(g.kind, g.cap) for g in labels.gates}
    # The pinned public CapRecord uses a prose reason, not a machine gate ID.
    # Category identifies each registered hard gate; its observed cap is still
    # checked independently, including triggered gates that do not bind the score.
    gate_kinds = {"leakage": "direct_leakage", "inference_mismatch": "missing_at_inference",
                  None: "invalid_timestamp"}
    actual = {(gate_kinds.get(g["category"], "unregistered:" + str(g["category"])), float(g["value"]))
              for g in caps if g["type"] == "hard_gate"}
    seen = {(f["metadata"]["check_id"], f["metadata"]["subject_key"]) for f in report["findings"]}
    suppression = sum((s.winner, s.subject) in seen and (s.loser, s.subject) not in seen for s in labels.suppressions)
    expected_categories = labels.expected_category_caps
    actual_categories = {g["category"]: float(g["value"]) for g in caps if g["type"] == "category_cap"}
    expected_columns = {f.subject.removeprefix("column:") for f in labels.findings if f.subject.startswith("column:")}
    actual_columns = {s.removeprefix("column:") for _, s in seen if s.startswith("column:")}
    union = expected_columns | actual_columns
    return {"gate_correctness": ratio(int(expected == actual), 1).model_dump(),
        "false_gates": sorted(k for k, _ in actual if k not in {name for name, _ in expected}),
        "missing_gates": sorted(k for k, _ in expected if k not in {name for name, _ in actual}),
        "incorrect_gate_caps": sorted(k for k, value in actual if k in {name for name, _ in expected} and (k, value) not in expected),
        "score_respects_gates": all(report["readiness_score"] <= value for _, value in expected),
        "category_caps_correct": actual_categories == expected_categories,
        "suppression_correctness": ratio(suppression, len(labels.suppressions)).model_dump(),
        "missing_independent_duplicate_subjects": sorted(f.subject for f in labels.findings
            if f.check_id == "quality.duplicates" and (f.check_id, f.subject) not in seen),
        "affected_columns_equal": expected_columns == actual_columns,
        "affected_columns_jaccard": len(expected_columns & actual_columns)/len(union) if union else 1.0}


def evaluate_scenario(opportunities: list[Opportunity], labels: VariantExpectations, report: dict | None, *, failure_kind=None) -> dict:
    """Scenario/all-required denominators stay separate from per-check support."""
    findings = report["findings"] if report is not None else []
    result = {"finding_evaluation": "EVALUABLE" if report is not None else "UNEVALUABLE",
              "gates_and_suppression": evaluate_gates_and_suppression(labels, report) if report is not None else None}
    for track in ("normative", "controlled_condition"):
        positives = [o for o in opportunities if o.track == track and o.positive]
        detected = sum(any(f["metadata"]["check_id"] in o.matching_check_ids and
                           f["metadata"]["subject_key"] == o.subject for f in findings) for o in positives)
        frame = [o for o in opportunities if o.track == track]
        coverage = opportunity_coverage(frame, report, failure_kind=failure_kind)
        evaluable = report is not None and bool(positives)
        result[track] = {**coverage.model_dump(), "positive_opportunities": len(positives),
            "detected_opportunities": detected if report is not None else None,
            "scenario_detection": ratio(int(detected > 0), int(evaluable)).model_dump(),
            "all_required_detected": ratio(int(evaluable and detected == len(positives)), int(evaluable)).model_dump(),
            "end_to_end_detection_yield": ratio(detected, len(positives)).model_dump() if track == "controlled_condition" else None}
    if report is None:
        return {**result, "out_of_frame_finding_ids": None, "labeled_confidence_correct": None, "normative_conformant": None}
    normative = evaluate_frame([o for o in opportunities if o.track == "normative"], report)
    framed = {(c, o.subject) for o in opportunities if o.track == "normative" for c in o.matching_check_ids}
    result["out_of_frame_finding_ids"] = sorted(f["id"] for f in findings if (
        f["metadata"]["check_id"], f["metadata"]["subject_key"]) not in framed)
    result["labeled_confidence_correct"] = all(any(f["metadata"]["check_id"] == label.check_id
        and f["metadata"]["subject_key"] == label.subject and float(f["confidence"]) == label.confidence
        for f in findings) for label in labels.findings if label.confidence is not None)
    result["normative_conformant"] = (not result["out_of_frame_finding_ids"] and all(
        m.fp == 0 and m.fn == 0 and m.severity_correctness.numerator == m.severity_correctness.denominator for m in normative)
        and result["gates_and_suppression"]["gate_correctness"]["value"] == 1.0
        and result["gates_and_suppression"]["score_respects_gates"]
        and result["gates_and_suppression"]["category_caps_correct"] and result["labeled_confidence_correct"]
        and result["gates_and_suppression"]["suppression_correctness"]["numerator"] == len(labels.suppressions))
    return result

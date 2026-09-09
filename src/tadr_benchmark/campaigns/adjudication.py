"""Verify the approved overlay from immutable public annotations and reports.

Supplemental operator scripts are preserved as evidence, never imported/executed.
"""

import copy
import json
from collections import Counter, defaultdict

from ..companions import VariantExpectations
from ..evaluation.metrics import Opportunity, aggregate_detection, evaluate_frame, evaluate_scenario, ratio
from ..reporting.queries import TABLE_COLUMNS, coverage_cells, csv_bytes, ratio_cells
from ..serialization import canonical_bytes, sha256
from .publication import ALPHA_ADJUDICATION_CHECKSUM, require, verify_checksums


def add_ratio(n, d):
    return ratio(n, d).model_dump(mode="json")


BUNDLE_FILES = {
    "adjudication.json", "corrected_normative_annotations.json",
    "adjudicated_scenario_metrics.json", "practical_event_key.json",
    "contract_basis.json", "adjudication_provenance.json", "evidence_preservation.json",
    "summary.json", "checksums.sha256", "ADJUDICATION_REVIEW.md",
    "alpha_v1_adjudicate.py", "alpha_v1_rules.py", "alpha_v1_review.py",
    "source_audit.json", "contract_audit.json",
    "tables/adjudicated_scenario_matrix.csv", "tables/adjudicated_detection_by_check.csv",
}


def verify_adjudication(evidence, bundle: dict[str, bytes], scientific_review: bytes) -> dict:
    verify_checksums(bundle)
    require(set(bundle) == BUNDLE_FILES, "complete adjudication bundle is required")
    inputs = evidence.inputs
    if inputs.manifest.campaign_id == "ALPHA_BENCHMARK_V1":
        # This review-approved overlay is immutable evidence, not a fresh label proposal.
        require(sha256(bundle["checksums.sha256"]) == ALPHA_ADJUDICATION_CHECKSUM,
                "approved Alpha adjudication bundle changed")
    def read(name):
        return json.loads(bundle[name])
    provenance = read("adjudication_provenance.json")
    original = evidence.artifacts
    require(provenance["scientific_execution_revision"] == inputs.manifest.benchmark_git_commit
            and provenance["benchmark_processing_revision"] == evidence.processing.processing_git_commit,
            "adjudication provenance revision mismatch")
    require(provenance["original_candidate_checksums_sha256"] == sha256(original["checksums.sha256"])
            and provenance["original_processing_provenance_sha256"] == sha256(original["processing_provenance.json"])
            and provenance["original_scientific_review_sha256"] == sha256(scientific_review),
            "adjudication original evidence binding mismatch")
    for name, digest in provenance["processor_artifacts"].items():
        require(name in BUNDLE_FILES and sha256(bundle[name]) == digest, "adjudication script content hash mismatch")
    require(set(provenance["processor_artifacts"]) == {
        "alpha_v1_adjudicate.py", "alpha_v1_rules.py", "alpha_v1_review.py"},
        "adjudication script inventory mismatch")
    require(not provenance["scientific_execution_changed"] and provenance["scientific_invocations"] == 0
            and provenance["target_imports"] == 0, "adjudication changed scientific execution")
    contract = read("contract_basis.json")
    require(contract["target_installation_artifact_sha256"] == inputs.manifest.target_installation_artifact_sha256
            and contract["target_algorithm_version"] == inputs.manifest.target_algorithm_version
            and contract["target_baseline_revision"] == inputs.manifest.target_baseline_revision
            and contract["basis_precedes_scientific_execution"], "adjudication contract binding mismatch")
    require(contract["static_member_verification"] == read("contract_audit.json"),
            "contract audit differs from declared basis")
    preservation = read("evidence_preservation.json")
    hashes = {name: sha256(raw) for name, raw in original.items()}
    require(preservation["original_candidate_file_hashes_before"] == hashes
            and preservation["original_candidate_file_hashes_after"] == hashes,
            "adjudication rewrote original candidate evidence")
    require(preservation["attempts_sha256"] == hashes["attempts.jsonl"]
            and preservation["instrumentation_sha256"] == hashes["instrumentation.jsonl"]
            and preservation["source_audit"] == read("source_audit.json"),
            "adjudication ledger, instrumentation or source audit changed")

    record = read("adjudication.json")
    results = read("summary.json")
    require(record["effect_on_derived_metrics"] == results
            and record["original_annotation_artifact_sha256"] == hashes["expectations.json"]
            and record["original_scenario_matrix_sha256"] == hashes["tables/scenario_matrix.csv"],
            "adjudication original annotation binding mismatch")
    require(record["original_result_label"] == "ORIGINAL PREREGISTERED-LABEL RESULT"
            and record["corrected_result_label"] == "ADJUDICATED PINNED-CONTRACT RESULT",
            "original/adjudicated result distinction is missing")
    corrected = read("corrected_normative_annotations.json")
    changed_metrics = read("adjudicated_scenario_metrics.json")
    corrections = {item["scenario_id"]: item for item in record["corrections"]}
    require(len(corrections) == len(record["corrections"]), "duplicate adjudication correction")
    labels = {item.scenario_id: item for item in inputs.expectations}
    selected = {r.scenario_id: r for r in inputs.runs if r.phase == "measurement"
                and r.repeat_index == 0 and r.determinism_case_id == "standard"}
    matrix = copy.deepcopy(evidence.tables["scenario_matrix.csv"])
    before_labels, after_labels, before_metrics, after_metrics, reports = {}, {}, {}, {}, {}
    old_members, new_members = [], []
    practical = read("practical_event_key.json")
    practical_map = {item["scenario_id"]: item for item in practical}
    require(len(practical_map) == len(practical), "duplicate practical event_key record")
    for row in matrix:
        if row["family"] in {"sampling", "scale"}:
            continue
        sid = row["scenario_id"]
        old_label = next(v for v in labels[sid].normative if v.variant_id == "full_reference")
        old_frame = row["opportunity_frames"]["full_reference"]
        require(sid in corrected, "missing corrected annotation")
        new_label = VariantExpectations.model_validate(corrected[sid])
        new_frame = copy.deepcopy(old_frame)
        if sid in corrections:
            change = corrections[sid]
            require(change["original_annotation"] == old_label.model_dump(mode="json")
                    and change["corrected_annotation"] == corrected[sid]
                    and change["original_normative_frame"] == [o for o in old_frame if o["track"] == "normative"]
                    and change["scenario_sha256"] == labels[sid].scenario_sha256
                    and not change["scientific_execution_changed"],
                    "adjudication correction does not bind original labels")
            physical = [o for o in old_frame if o["track"] == "controlled_condition"]
            require(change["physical_frame_sha256_unchanged"] == sha256(canonical_bytes(physical)),
                    "adjudication changed physical opportunity frame")
            new_frame = sorted(physical + change["corrected_normative_frame"], key=lambda o: o["opportunity_id"])
        else:
            require(new_label == old_label, "unrecorded normative correction")
        run = selected[sid]
        report = json.loads(inputs.reports[run.run_id])
        reports[sid] = report
        typed_old = [Opportunity.model_validate(v) for v in old_frame]
        typed_new = [Opportunity.model_validate(v) for v in new_frame]
        before_labels[sid], after_labels[sid] = old_label.model_dump(mode="json"), new_label.model_dump(mode="json")
        before_metrics[sid] = evaluate_scenario(typed_old, old_label, report)
        after_metrics[sid] = evaluate_scenario(typed_new, new_label, report)
        require(before_metrics[sid] == row["scenario_metrics"]["full_reference"]
                and before_metrics[sid]["controlled_condition"] == after_metrics[sid]["controlled_condition"],
                "adjudication original or physical metrics changed")
        for cutoff in ("INFO", "LOW"):
            before, after = evaluate_frame(typed_old, report, cutoff=cutoff), evaluate_frame(typed_new, report, cutoff=cutoff)
            require([m for m in before if m.track == "controlled_condition"] ==
                    [m for m in after if m.track == "controlled_condition"], "physical metrics changed")
            old_members.extend((run.source_format, run.analysis_variant, m) for m in before)
            new_members.extend((run.source_format, run.analysis_variant, m) for m in after)
        row["normative_expectations"] = [corrected[sid]]
        row["opportunity_frames"]["full_reference"] = new_frame
        row["scenario_metrics"]["full_reference"] = after_metrics[sid]
        if sid in corrections:
            effect = corrections[sid]["effect_on_derived_metrics"]
            require(effect == {"original": before_metrics[sid], "adjudicated": after_metrics[sid],
                               "normative_opportunity_change": len(new_frame) - len(old_frame),
                               "physical_opportunity_change": 0}, "adjudication metric effect mismatch")
        if sid in practical_map:
            p = practical_map[sid]
            finding = next(f for f in report["findings"] if f["id"] == "schema.parse_failures::column:event_key")
            require(p["observed_finding"] == finding and p["readiness"] == report["readiness_score"]
                    and p["canonical_report_sha256"] == run.canonical_report_sha256
                    and p["source_file_sha256"] == run.source_file_sha256
                    and not p["physical_truth_changed"] and not p["primary_clean_control_eligible"]
                    and not labels[sid].primary_clean_control_eligible and "ADVERSE" in p["interpretation"],
                    "practical adverse event_key evidence changed")
    require(set(corrected) == set(after_metrics) == set(changed_metrics)
            and changed_metrics == after_metrics and set(corrections) <= set(after_metrics),
            "adjudicated scenario metrics or inventory mismatch")
    require(results["event_key_representation_cells"] == len(practical)
            and results["event_key_logical_pairs"] == len({p["logical_case_id"] for p in practical}),
            "event_key representation/logical counts mismatch")
    for name, metrics, annotations, members in (
        ("original_preregistered_label_result", before_metrics, before_labels, old_members),
        ("adjudicated_pinned_contract_result", after_metrics, after_labels, new_members),
    ):
        require(results[name] == summarize(members, metrics, annotations, reports),
                "adjudication summary does not derive from reports")
    require(results["remaining_nonconformant_scenario_ids"] ==
            sorted(sid for sid, m in after_metrics.items() if not m["normative_conformant"]),
            "remaining conformance inventory mismatch")
    require(bundle["tables/adjudicated_scenario_matrix.csv"] == csv_bytes(TABLE_COLUMNS["scenario_matrix.csv"], matrix),
            "adjudicated scenario table is stale")
    require(bundle["tables/adjudicated_detection_by_check.csv"] ==
            csv_bytes(TABLE_COLUMNS["detection_by_check.csv"], detection_table(new_members)),
            "adjudicated detection table is stale")
    require(original["tables/detection_by_check.csv"] ==
            csv_bytes(TABLE_COLUMNS["detection_by_check.csv"], detection_table(old_members)),
            "original detection table changed")
    return results


def detection_table(members):
    grouped = defaultdict(list)
    for fmt, variant, member in members:
        grouped[(member.track, member.check_id, member.stratum, fmt, variant,
                 member.severity_cutoff)].append(member)
    result = []
    names = {
        "conditional_precision": "conditional_precision", "conditional_recall": "conditional_recall",
        "conditional_fpr": "conditional_fpr", "scenario_detection": "scenario_detection",
        "all_required_detected": "all_required", "severity_correctness": "severity",
        "detection_and_severity": "detection_severity", "localization": "localization",
    }
    for (track, check, stratum, fmt, variant, cutoff), values in sorted(grouped.items()):
        metrics = aggregate_detection(values)
        row = dict(track=track, check_id=check, stratum=stratum, format=fmt,
                   analysis_variant=variant, severity_cutoff=cutoff, **coverage_cells(metrics),
                   **{key: getattr(metrics, key) for key in ("tp", "fp", "fn", "tn")},
                   **ratio_cells("end_to_end_detection_yield", metrics.end_to_end_detection_yield))
        for name, prefix in names.items():
            row.update(ratio_cells(prefix, getattr(metrics, name)))
        row.update(out_of_frame_finding_ids=metrics.out_of_frame_finding_ids,
                   mapped_detector_details=metrics.mapped_detector_details)
        result.append(row)
    return result


def summarize(members, scenario_metrics, annotations, reports):
    results = {}
    for track in ("normative", "controlled_condition"):
        for cutoff in ("INFO", "LOW"):
            for fmt in ("combined", "csv", "parquet"):
                group = [m for f, _, m in members if m.track == track and m.severity_cutoff == cutoff
                         and (fmt == "combined" or f == fmt)]
                sums = {key: sum(getattr(m, key) for m in group) for key in (
                    "tp", "fp", "fn", "tn", "planned_opportunities", "evaluable_opportunities",
                    "planned_positive_opportunities")}
                results["/".join((track, cutoff, fmt))] = {
                    **sums,
                    "conditional_precision": add_ratio(sums["tp"], sums["tp"] + sums["fp"]),
                    "conditional_recall": add_ratio(sums["tp"], sums["tp"] + sums["fn"]),
                    "conditional_fpr": add_ratio(sums["fp"], sums["fp"] + sums["tn"]),
                    "successful_report_coverage": add_ratio(sums["evaluable_opportunities"], sums["planned_opportunities"]),
                    "end_to_end_detection_yield": (add_ratio(sums["tp"], sums["planned_positive_opportunities"])
                                                  if track == "controlled_condition" else None),
                    "severity_correctness": add_ratio(sum(m.severity_correctness.numerator for m in group),
                                                       sum(m.severity_correctness.denominator for m in group)),
                }
    values = list(scenario_metrics.values())
    gates = [m["gates_and_suppression"] for m in values]
    # Independently count exact expected Findings, severities, gates and suppression
    # directly from the corrected labels and original report fields.
    independent = Counter()
    for sid, label in annotations.items():
        report = reports[sid]
        seen = {(f["metadata"]["check_id"], f["metadata"]["subject_key"]): f for f in report["findings"]}
        for finding in label["findings"]:
            actual = seen.get((finding["check_id"], finding["subject"]))
            independent["expected_findings"] += 1
            independent["matched_expected_findings"] += actual is not None
            independent["correct_expected_severity"] += actual is not None and actual["severity"].upper() == finding["severity"]
            if finding["confidence"] is not None:
                independent["explicit_confidence_labels"] += 1
                independent["correct_explicit_confidence"] += actual is not None and float(actual["confidence"]) == finding["confidence"]
        gate_kind = {"leakage": "direct_leakage", "inference_mismatch": "missing_at_inference", None: "invalid_timestamp"}
        observed = {(gate_kind.get(g["category"], "unknown"), float(g["value"]))
                    for g in report["score_breakdown"]["caps_applied"] if g["type"] == "hard_gate"}
        expected = {(g["kind"], float(g["cap"])) for g in label["gates"]}
        independent["gate_set_cells"] += 1
        independent["correct_gate_sets"] += observed == expected
        independent["expected_gate_occurrences"] += len(expected)
        independent["matched_gate_occurrences"] += len(expected & observed)
        independent["unexpected_gate_occurrences"] += len(observed - expected)
        for suppression in label["suppressions"]:
            independent["suppression_opportunities"] += 1
            independent["correct_suppression"] += ((suppression["winner"], suppression["subject"]) in seen
                                                   and (suppression["loser"], suppression["subject"]) not in seen)
    info = results["normative/INFO/combined"]
    require(info["tp"] == independent["matched_expected_findings"], "expected Finding count mismatch")
    require(info["planned_positive_opportunities"] == independent["expected_findings"], "positive opportunity mismatch")
    require(info["severity_correctness"]["numerator"] == independent["correct_expected_severity"], "severity count mismatch")
    return {
        "whole_cell_normative_conformance": add_ratio(sum(m["normative_conformant"] for m in values), len(values)),
        "gate_correctness": add_ratio(sum(g["gate_correctness"]["numerator"] for g in gates), len(gates)),
        "category_caps_correctness": add_ratio(sum(g["category_caps_correct"] for g in gates), len(gates)),
        "score_respects_gates": add_ratio(sum(g["score_respects_gates"] for g in gates), len(gates)),
        "suppression_correctness": add_ratio(sum(g["suppression_correctness"]["numerator"] for g in gates),
                                           sum(g["suppression_correctness"]["denominator"] for g in gates)),
        "out_of_frame_findings": sum(len(m["out_of_frame_finding_ids"]) for m in values),
        "independent_report_field_checks": dict(independent), "detection": results,
        "normative_scenario_detection": add_ratio(sum(m["normative"]["scenario_detection"]["numerator"] for m in values),
                                                 sum(m["normative"]["scenario_detection"]["denominator"] for m in values)),
        "normative_all_required": add_ratio(sum(m["normative"]["all_required_detected"]["numerator"] for m in values),
                                           sum(m["normative"]["all_required_detected"]["denominator"] for m in values)),
    }

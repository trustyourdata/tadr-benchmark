"""Deterministic public interpretation of the preserved Alpha evidence layers."""

import json
from collections import Counter, defaultdict


def fraction(value):
    n, d = value["numerator"], value["denominator"]
    return f"{n}/{d}" + (f" ({100*n/d:.4f}%)" if d else " (undefined)")


def publication_report(evidence, adjudication, provenance, manifest) -> str:
    inputs, tables = evidence.inputs, evidence.tables
    before = adjudication["original_preregistered_label_result"]
    after = adjudication["adjudicated_pinned_contract_result"]
    physical = after["detection"]["controlled_condition/INFO/combined"]
    independent = after["independent_report_field_checks"]
    sampling = tables["sampling_fidelity.csv"]
    disagreements = [r for r in sampling if r["finding_agreement"] != 1]
    formats = tables["format_equivalence.csv"]
    mismatches = [r for r in formats if r["eligible"] and not (
        r["canonical_bytes_equal"] if r["comparison_kind"] == "string_format" else r["semantic_projection_equal"])]
    format_counts = Counter(r["comparison_kind"] for r in mismatches)
    decision_equal = all(all(value for field, value in r["field_agreement"].items()
                             if field != "dataset_profile") for r in mismatches)
    clean_ids = {e.scenario_id for e in inputs.expectations if e.primary_clean_control_eligible}
    clean = [r for r in inputs.runs if r.scenario_id in clean_ids and r.phase == "measurement"
             and r.repeat_index == 0 and r.determinism_case_id == "standard"]
    clean_empty = sum(not json.loads(inputs.reports[r.run_id])["findings"] for r in clean)
    pairs = defaultdict(list)
    for run in inputs.runs:
        if run.execution_group_id in {"determinism_small", "determinism_sampled"}:
            pairs[(run.scenario_id, run.analysis_variant, run.determinism_case_id)].append(run)
    repeated = [v for v in pairs.values() if len(v) == 2 and sorted(r.repeat_index for r in v) == [0, 1]]
    identical = sum(inputs.reports[v[0].run_id] == inputs.reports[v[1].run_id] for v in repeated)
    determinism = tables["determinism.csv"]
    matching = sum(r["canonical_bytes_equal"] for r in determinism)
    gaps = [i.maximum_sample_gap_seconds for i in evidence.instrumentation
            if i.maximum_sample_gap_seconds is not None]
    original = "ORIGINAL PREREGISTERED-LABEL RESULT"
    corrected = "ADJUDICATED PINNED-CONTRACT RESULT"
    publication_revision = provenance.publication_assembly_revision or "unresolved (pre-commit stage)"
    lines = [
        f"# {manifest.campaign_id}", "",
        "Controlled synthetic evaluation of TADR Core Alpha / Check Set A.", "",
        ("Publication stage: assembly revision and freeze date are unresolved; no immutable release has been created."
         if provenance.state == "staged" else f"Frozen release: {manifest.frozen_date}."), "",
        f"**{original}: whole-cell normative conformance {fraction(before['whole_cell_normative_conformance'])}.**", "",
        f"**{corrected}: whole-cell normative conformance {fraction(after['whole_cell_normative_conformance'])}.**", "",
        f"**Physical detection: {fraction(physical['conditional_recall'])}; {physical['fn']} physical misses remain.** "
        "Pinned-contract conformance is a different metric and does not replace physical detection.", "",
        "## Scientific history and provenance", "",
        "Original physical/design ground truth and preregistered normative labels preceded execution. Normative adjudication occurred after execution and derives "
        "from the pre-existing Algorithm 1.0 contract. No target execution changed; physical truth and scientific inputs "
        "did not change; canonical reports, attempts, instrumentation and diagnostics were unchanged. The original "
        "234/320 label result is retained as historical scientific-design evidence, not overwritten.", "",
        "| Provenance role | Binding |", "| --- | --- |",
        f"| Scientific execution | {provenance.scientific_execution_revision} |",
        f"| Historical processing/aggregation | {provenance.historical_processing_revision} |",
        f"| Publication assembly | {publication_revision} |",
        f"| Target | {manifest.target_name} {manifest.target_package_version}; Algorithm {manifest.target_algorithm_version}; "
        f"{manifest.target_threshold_profile}; AnalysisBundle {manifest.target_bundle_protocol}; baseline {manifest.target_baseline_revision} |",
        f"| Proprietary installation artifact SHA-256 | {manifest.target_installation_artifact_sha256} |", "",
        "See [execution provenance](execution_provenance.json), [historical processing provenance](processing_provenance.json), "
        "[publication provenance](publication_provenance.json), [execution environment](environment.json) and "
        "[publication inventory](publication_inventory.json). The READY manifest under history is the original launch declaration; "
        "its NOT YET RUN notes do not describe this completed experiment.", "",
        "The evaluated tadr-core implementation is proprietary. This repository distributes neither Core source nor private wheel bytes. "
        "Re-execution and independent semantic inspection of the implementation require authorized artifact access. Public generators, "
        "recipes, ground truth and dataset identities support regeneration; generated source CSV/Parquet files are excluded from this "
        "release. Source-level rebuilding of proprietary Core from public artifacts is unavailable.", "",
        "## Original and adjudicated annotations", "",
        f"The supplemental overlay records {adjudication['correction_counts'].get('category_cap_annotation_defect', 0)} category-cap annotation defects "
        f"and {adjudication['correction_counts'].get('event_key_pinned_contract_frame_correction', 0)} event_key normative-frame disagreements. "
        "Category caps follow the existing weighted-severity/confidence scoring rule. The event name heuristic treats event_key as a "
        "datetime candidate. The correction adds normative check/subject opportunities without changing physical truth or primary-clean membership.", "",
        "| Metric | Original | Adjudicated |", "| --- | --- | --- |",
    ]
    for key, label in (
        ("whole_cell_normative_conformance", "Whole-cell normative conformance"),
        ("category_caps_correctness", "Category-cap annotation correctness"),
        ("gate_correctness", "Hard-gate correctness"),
        ("suppression_correctness", "Suppression"),
    ):
        lines.append(f"| {label} | {fraction(before[key])} | {fraction(after[key])} |")
    lines += [
        f"| INFO normative opportunity coverage | {fraction(before['detection']['normative/INFO/combined']['successful_report_coverage'])} | "
        f"{fraction(after['detection']['normative/INFO/combined']['successful_report_coverage'])} |", "",
        "Inspect [all old/corrected annotations and metric effects](adjudication_v1/adjudication.json), "
        "[corrected normative labels](adjudication_v1/corrected_normative_annotations.json), "
        "[adjudicated scenario metrics](adjudication_v1/adjudicated_scenario_metrics.json), "
        "[original/adjudicated summary](adjudication_v1/summary.json), "
        "[adjudicated scenario table](adjudication_v1/tables/adjudicated_scenario_matrix.csv), "
        "[adjudicated detection table](adjudication_v1/tables/adjudicated_detection_by_check.csv), "
        "[contract basis](adjudication_v1/contract_basis.json) and "
        "[evidence preservation](adjudication_v1/evidence_preservation.json).", "",
        "Root expectations.json, runs.jsonl detection fields, summary.json, tables and figures retain the ORIGINAL "
        "PREREGISTERED-LABEL RESULT. They must not be described as adjudicated values. The "
        "[original candidate report](history/candidate_REPORT.md), [READY manifest](history/ready_manifest.json), "
        "[original checksum manifest](history/candidate_checksums.sha256) and "
        "[original scientific review](history/ALPHA_BENCHMARK_V1_SCIENTIFIC_RESULT_REVIEW.md) preserve historical content. "
        "Their old banners and relative links are archival; the [reproduction note](ADJUDICATION_REPRODUCTION.md) supplies the current path mapping.", "",
        "## Principal adverse findings", "",
        f"**Physical sensitivity remains {physical['tp']}/{physical['planned_positive_opportunities']} "
        f"({100*physical['tp']/physical['planned_positive_opportunities']:.4f}%), with {physical['fn']} physical misses.** "
        "Below-threshold, support/collapse, nonreciprocal leakage, allowlisting and split-policy cases retain their original strata. "
        "The shared entity condition remains one physical opportunity; normative detector identity and suppression remain separate.", "",
        f"**Adverse event_key specificity: {adjudication['event_key_representation_cells']} representation cells / "
        f"{adjudication['event_key_logical_pairs']} logical pairs.** Valid `event_<integer>` identifiers triggered HIGH "
        "schema.parse_failures::column:event_key warnings. These are normatively expected by the pinned Alpha heuristic and "
        "practically adverse specificity behavior, not malformed physical datetime values or a favorable result. The isolated "
        "10.04 schema penalty gives quiet keyed/group cases readiness 90 and report confidence 81; absolute family scores include "
        "that background. [All original event_key Findings and scores](adjudication_v1/practical_event_key.json) remain visible. "
        "None of these cells is added post hoc to primary-clean FPR. Primary-clean false-positive rate remains 0/226 for the eight "
        "preregistered controls; that narrow result does not establish general absence of unwanted warnings.", "",
        f"**Sampling: {len(sampling)-len(disagreements)}/{len(sampling)} reference/bounded Finding sets agree exactly; "
        f"{len(disagreements)} disagree.** The deterministic HEAD_STRIDE_V1 geometry can miss conditions or change threshold eligibility. "
        "Exact repetition can repeat the same blind spot.", "",
        "| Disagreeing sampling cell | Readiness full → bounded | Findings/gates retained as observed |",
        "| --- | --- | --- |",
    ]
    for row in sorted(disagreements, key=lambda r: r["scenario_id"]):
        ref = json.loads(inputs.reports[row["reference_run_id"]])
        bounded = json.loads(inputs.reports[row["sampled_run_id"]])
        description = "See original paired reports and diagnostics; no underlying data improvement is inferred."
        if row["scenario_id"].startswith("sampling.leakage.head."):
            description = "CRITICAL leakage Finding disappears; hard gate disappears. This is a negative sampling result."
        lines.append(f"| {row['scenario_id']} | {ref['readiness_score']} → {bounded['readiness_score']} | {description} |")
    lines += [
        "", "The leakage head case's **60 → 100** change is not improved data quality. "
        "See [sampling fidelity](tables/sampling_fidelity.csv) and [diagnostic primitives](tables/sampling_primitives.csv).", "",
        f"**Strict format comparison: {len(mismatches)} mismatches — {format_counts['string_format']} CSV/pqstr and "
        f"{format_counts['native_projection']} native projections.** "
        f"Decision fields remained equal across these mismatches: {'yes' if decision_equal else 'no'}. "
        "Empty-token/typed-null and typed string-statistic differences affect dataset_profile. Findings, readiness, risks, "
        "confidence, gates/caps, analysis_stats and remediation retain the observed agreement. "
        "The [preregistered strict comparison](tables/format_equivalence.csv) is not replaced by a post hoc normalized metric.", "",
        "**Scoring limitations:** numeric parser corruption 2000/10000 gives readiness 89 and Finding confidence .70; "
        "4000/10000 gives readiness 90 and confidence .62; 6000/10000 loses numeric dominance and gives readiness 100. "
        "This is parser/scoring non-monotonicity. A collapsed class can escape the diversity-dependent imbalance check. "
        "Readiness and confidence are not calibrated damage or safety measures. Remediation gains are heuristic estimates, "
        "not measured causal recovery or downstream model improvement.", "",
        "## Supported positive observations and exact scope", "",
        f"- {len(inputs.runs)}/{len(inputs.runs)+len(inputs.failures)} successful selected primary reports; "
        f"{evidence.summary.infrastructure_retries} retries, "
        f"{evidence.summary.resolved_infrastructure_failures} resolved infrastructure failures and "
        f"{len(inputs.failures)} terminal failures, including timeouts/resource aborts.",
        f"- {len(inputs.diagnostics)}/{len(inputs.diagnostics)} retained diagnostics.",
        f"- Adjudicated expected Finding matches: {independent['matched_expected_findings']}/{independent['expected_findings']}; "
        f"severity matches: {independent['correct_expected_severity']}/{independent['expected_findings']}.",
        f"- Hard-gate correctness: {fraction(after['gate_correctness'])}; suppression: {fraction(after['suppression_correctness'])}.",
        f"- Primary clean controls with zero Findings: {clean_empty}/{len(clean)}.",
        f"- Selected context/repeat pairs byte-identical: {identical}/{len(repeated)}; declared determinism comparisons matching: {matching}/{len(determinism)}.", "",
        "Singleton groups are **not repeat-tested**. Historical summary booleans denote within-group equality and do not demonstrate "
        "repeatability for one observation. These positive findings apply only to this constructed corpus, its declared contexts/repeats "
        "and scientific environment. They do not establish real-world accuracy, unbiased population estimates, calibration, production "
        "safety, regulatory suitability, downstream model quality or state-of-the-art performance.", "",
        "## Performance and measurement limits", "",
        "Execution used Ubuntu 24.04 under WSL2, Linux x86_64, Python 3.11.9, four Polars threads and native ext4 storage. "
        "Results are WSL2-specific; native-Linux equivalence is not claimed. Filesystem cache was recently prepared/uncontrolled, "
        "not cold-cache. Runtime brackets public analysis only, with generation/startup/serialization/evaluation outside the bracket. "
        "Sampled RSS sums the worker tree, excludes the supervisor, includes worker baseline memory and can miss short-lived peaks. "
        "It is not the true continuous peak or a hard memory guarantee.", "",
        f"Requested RSS interval: 0.01 seconds. Actual maximum observed gap: {max(gaps) if gaps else 'unavailable'} seconds. "
        "Per-run counts, gaps, completion and context acknowledgements remain in "
        "[instrumentation.jsonl](instrumentation.jsonl). Warmups remain in runs.jsonl and are excluded from measured aggregates.", "",
        "| Scale cell | Measured n | Original seconds, repeat order | Median s | Range s | Evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in sorted(tables["scale_performance.csv"], key=lambda r: r["scenario_id"]):
        strength = "n=2 weak descriptive evidence; two-point MAD is not interpreted" if row["weak_evidence"] else "descriptive repeated measurements"
        lines.append(f"| {row['scenario_id']} | {row['measured_successes']} | {json.dumps(row['runtime_values_seconds'])} | "
                     f"{row['runtime_median_seconds']} | {row['runtime_min_seconds']}–{row['runtime_max_seconds']} | {strength} |")
    lines += [
        "", "The 5M case has **n=2 weak descriptive evidence**, zero warmups and both raw measurements retained. "
        "Small repeat counts do not support inferential performance claims. Fixed sampled population does not remove full-scan/source costs; "
        "cross-mode throughput is not an equal-work speedup. [Original scale table](tables/scale_performance.csv) retains all metrics.", "",
        "## Artifact queries, figures and reproduction", "",
        "All original tables and SVG bytes are preserved. Figure regeneration uses selected outcomes ordered by stable attempt_id, "
        "including tied x-values; this changes neither scientific execution order nor canonical RunSpec/run serialization. "
        "The figures depict original-label queries; the adjudicated tables above remain a separate layer. "
        "[Original summary](summary.json) and [summary table](tables/summary.csv) retain original aggregation.", "",
        *[f"- [{name}](tables/{name})" for name in sorted(tables)], "",
        *[f"![Original {name.removesuffix('.svg').replace('_', ' ')}](figures/{name})" for name in sorted(evidence.figures)], "",
        "Verify the complete outer [checksums](checksums.sha256), original-candidate archive mapping and "
        "[adjudication inner checksums](adjudication_v1/checksums.sha256). "
        "[ADJUDICATION_REPRODUCTION.md](ADJUDICATION_REPRODUCTION.md) explains public input reconstruction, script hashes, "
        "historical Windows annotation processing and the proprietary target boundary. "
        "Publication provenance is separate from both historical revisions; no fictitious commit is assigned to operator scripts.", "",
    ]
    return "\n".join(lines)


def adjudication_reproduction(bundle: dict[str, bytes]) -> str:
    provenance = json.loads(bundle["adjudication_provenance.json"])
    script_rows = "\n".join(f"| [{name}](adjudication_v1/{name}) | {digest} |"
                            for name, digest in sorted(provenance["processor_artifacts"].items()))
    return f"""# Adjudication reproduction

The ORIGINAL PREREGISTERED-LABEL RESULT is retained in root expectations.json,
runs.jsonl evaluation fields, summary.json, tables and original figures.
The ADJUDICATED PINNED-CONTRACT RESULT is supplemental: it records post-execution
normative corrections derived from the pre-existing Algorithm 1.0 contract.
No physical truth, primary-clean denominator, input, report or target execution changed.

## Artifact roles and original path mapping

Read [publication_inventory.json](publication_inventory.json) for the exact file
inventory and original_candidate_mapping. Original manifest.json, REPORT.md and
checksums.sha256 map respectively to history/ready_manifest.json,
history/candidate_REPORT.md and history/candidate_checksums.sha256. Every other
original candidate file retains its root-relative path.

The original scientific review is preserved under history. Its relative links
and the bundled ADJUDICATION_REVIEW.md links describe the historical operator
layout. Historical alpha_execution/candidate/X and ../candidate/X references map
to the original-candidate mapping above; alpha_execution/adjudication_v1/X maps
to adjudication_v1/X. Use the working links in the public [REPORT](REPORT.md).
Historical NOT READY/NOT FROZEN banners are original review history, not the
current publication state.

## Pure correction and evaluation reconstruction

No target package import is needed. Using the public benchmark code identified
in publication_provenance.json, verify_frozen validates the complete release;
verify_publication also supports an explicitly allowed unresolved dry-run stage.
Neither function invokes TADR.

To independently reconstruct the annotation transformation:

1. Load original scenarios, expectations and the full_reference opportunity frame
   from the original tables/scenario_matrix.csv.
2. Import only correct_annotation from the supplied alpha_v1_rules.py (public
   benchmark dependencies are required). Pass the scenario dictionary, original
   VariantExpectations dictionary and original frame. The function takes no report.
3. Compare the returned labels/frames to adjudication.json and
   corrected_normative_annotations.json. Keep the physical frame identical.
4. Select standard-context measured repeat zero for each correctness scenario.
   Apply benchmark evaluate_scenario/evaluate_frame to the unchanged canonical
   report and original/corrected normative labels separately. Compare results to
   adjudicated_scenario_metrics.json, both adjudicated tables and summary.json.
5. Retain 234/320 as original-label history and 320/320 as adjudicated conformance;
   retain the adverse practical_event_key.json observations and all physical misses.

The durable verifier reads the reviewed bundle as data and recomputes its metrics;
it never executes embedded operator scripts. The supplied pure rule module makes
the contract-based transformation independently inspectable/reconstructible.

## Supplemental script identities

| Script | SHA-256 |
| --- | --- |
{script_rows}

These operator bytes were not assigned a fictitious Git commit. Historical
benchmark processing revision remains {provenance['benchmark_processing_revision']}.
The annotation-processing environment in adjudication_provenance.json is the
actual historical Windows environment, distinct from the original Linux scientific
execution and processing environments.

The original alpha_v1_adjudicate.py wrapper assumes its original working-directory
layout, a clean historical checkout and environment recapture. It is not a portable
one-command verifier of an arbitrarily relocated directory. Use the durable
publication verifier or pure reconstruction above; do not rewrite historical
environment metadata to match the reviewing machine.

## Reproduction and proprietary boundary

Public recipes/generators and identities support source regeneration, but generated
source CSV/Parquet files are excluded. Exact source bytes require the recorded writer
stack; logical equality alone is not exact-file equality. Original SVG reproduction
requires recorded rendering dependencies and stable selected attempt_id ordering.

The tadr-core implementation and wheel remain proprietary and are not distributed.
Execution requires authorized access to the fingerprinted wheel. Independent semantic
inspection of its implementation also requires authorized artifact access. Named
contract symbols/member hashes and reviewed rules do not provide public Core source
or source-level rebuild reproducibility. Public benchmark aggregation and the
annotation overlay can be inspected and reproduced without executing Core.
"""

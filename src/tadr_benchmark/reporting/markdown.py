from pathlib import Path

from ..models import CampaignManifest, CampaignSummary


def campaign_report(manifest: CampaignManifest, summary: CampaignSummary, *, tables=(), figures=()) -> str:
    source_note = (
        "The evaluated TADR Core implementation is proprietary; an external party cannot "
        "rebuild the evaluated implementation from public source. Benchmark methodology, "
        "synthetic datasets, ground truth, scenario definitions, execution protocol, evaluation "
        "and published result artifacts are public. The exact target is identified by versioned "
        "metadata and the execution artifact SHA-256. This repository distributes neither the "
        "proprietary artifact nor its source code. Re-execution requires authorized artifact access.\n\n")
    artifact_note = (f"Installation artifact SHA-256: `{manifest.target_installation_artifact_sha256}`.\n\n"
                     if manifest.target_installation_artifact_sha256 else
                     "Installation artifact SHA-256: not recorded.\n\n")
    rows = ["| Scenario / variant | Runs | Runtime median (s) | MAD (s) | Peak RSS median (bytes) | Deterministic |",
            "| --- | ---: | ---: | ---: | ---: | --- |"]
    for group in summary.groups:
        rows.append(f"| {group.scenario_id} / {group.analysis_variant} / {group.determinism_case_id} | {group.measured_runs} | "
                    f"{group.runtime_median_seconds:.6g} | {group.runtime_mad_seconds:.6g} | "
                    f"{group.peak_rss_median_bytes:.6g} | {group.deterministic} |")
    return (f"# {manifest.campaign_id}\n\n"
            f"Target: `{manifest.target_name}` `{manifest.target_package_version}`. Algorithm `{manifest.target_algorithm_version}`, "
            f"profile `{manifest.target_threshold_profile}`, bundle `{manifest.target_bundle_protocol}`, "
            f"baseline `{manifest.target_baseline_revision}`.\n\n"
            f"Target source distribution: `{manifest.target_source_distribution}`. Run data SHA-256: "
            f"`{summary.run_data_sha256}`.\n\n"
            + source_note + artifact_note +
            f"Benchmark `{manifest.benchmark_package_version}` at `{manifest.benchmark_git_commit}`. "
            f"Environment and dependency identities are retained in environment.json.\n\n"
            "## Methodology and scenario matrix\n\n"
            "The frozen manifest, scenario snapshots and execution plan define the complete experiment. "
            "Ground truth precedes target execution. See the [frozen protocol](protocol.md) and "
            "[scenario matrix](tables/scenario_matrix.csv).\n\n"
            "## Detection, negative controls and boundary behavior\n\n"
            "See [summary table](tables/summary.csv) for matched/missed expectations, absent violations "
            "and unexpected Findings. Raw records retain each outcome; counts across repetitions "
            "are not independent samples or calibrated precision estimates.\n\n"
            "[Per-check metrics](tables/detection_by_check.csv) keep normative conformance and controlled-condition "
            "sensitivity separate, with fixed support counts and undefined rates left empty. "
            "Finding TP/FP/FN/TN and conditional precision/recall/FPR require a successful canonical report. "
            "A target failure without a report is UNEVALUABLE, never a negative prediction or Finding-level FN. "
            "Each conditional rate is accompanied by planned/evaluable/unevaluable opportunity counts, "
            "positive/negative successful-report coverage and terminal failures by category. "
            "End-to-end detection yield is detected positive physical opportunities divided by all planned positive "
            "physical opportunities, including those without reports; it is a separate system-level descriptive metric, not recall. "
            "[Clean controls](tables/clean_false_positives.csv) separate primary controls from specificity challenges; "
            "[boundaries](tables/threshold_boundaries.csv) retain exact construction numerators and denominators. "
            "Only the standard-context measured repeat zero enters these scientific queries; formats remain separate.\n\n"
            "## Score behavior, hard gates and suppression\n\n"
            "The table retains score ranges. Each raw record retains risks, ordered Findings, gates "
            "and remediations. Suppressed Findings cannot be reconstructed from final reports.\n\n"
            "See [score sweeps](tables/score_sweeps.csv), [composite interactions](tables/composite_interactions.csv) "
            "and [ordered remediation](tables/remediation.csv). These are observations, not a scoring oracle.\n\n"
            "## Determinism, runtime, throughput and peak RSS\n\n"
            + "\n".join(rows) + ("\n\n" if summary.groups else "\n\nNo successful performance measurements are available.\n\n") +
            "Warmups are retained in runs.jsonl and excluded from aggregates. MAD is the median "
            "absolute deviation. Canonical report disagreement is a determinism failure.\n\n"
            "See [determinism](tables/determinism.csv) and [first mismatch paths](tables/mismatch_paths.csv). "
            "Original byte disagreements remain visible even when parsed report fields agree. "
            "No target report is normalized to manufacture agreement.\n\n"
            "## Sampling fidelity and scalability\n\n"
            "Variants and scale points are explicit in the manifest. This summary does not infer "
            "full-versus-sampled fidelity or scaling behavior from unrelated scenarios.\n\n"
            "[Sampling fidelity](tables/sampling_fidelity.csv) and [primitive counts](tables/sampling_primitives.csv) "
            "report bounded-minus-full differences, including unavailable reasons. "
            "[Format equivalence](tables/format_equivalence.csv) separates strict string transports from native "
            "semantic-projection eligibility. [Scale performance](tables/scale_performance.csv) retains raw repeats, "
            "medians, ranges, unscaled MAD and explicit two-run weak evidence. Missing target outcomes have no invented timings.\n\n"
            "## Failure cases and limitations\n\n"
            f"Terminal coverage (including warmups): {summary.successful_runs} successful reports; "
            f"{summary.adverse_target_outcomes} adverse target outcomes retained in failures.jsonl. "
            "Failed analyses contribute no invented scores or performance values.\n\n"
            "Report availability is determined only by the selected scientific outcome. Resolved infrastructure retries "
            "remain operational history. Missing reports remain visible in the detection and clean-control coverage columns; "
            "high conditional agreement with incomplete coverage must not be interpreted as complete detection.\n\n"
            f"Operational history only: {summary.total_attempts} attempts, {summary.infrastructure_retries} infrastructure retries, "
            f"{summary.resolved_infrastructure_failures} resolved infrastructure failures. "
            "attempts.jsonl preserves every attempt; runs.jsonl/failures.jsonl contain only the first valid selected outcome. "
            "Retries never increase scientific support or performance repeat counts.\n\n"
            "Unexpected outcomes remain in the raw records. Synthetic cases cannot establish "
            "real-world prevalence, model quality or production guarantees. Sampled RSS can miss "
            "short peaks. Review outcomes before drawing scientific conclusions.\n\n"
            "## Reproduction\n\n"
            "Use the exact benchmark revision and fingerprinted target artifact, dependency versions in environment.json, "
            "scenario snapshots and run_specs.json. Verify checksums before analysis. "
            "Execution requires a resolved ready manifest and a verified working ledger.\n\n"
            "## Generated artifact queries\n\n"
            + "\n".join(f"- [{name}](tables/{name})" for name in sorted(tables)) + "\n\n"
            + "\n\n".join(f"![{name.removesuffix('.svg').replace('_', ' ')}](figures/{name})" for name in sorted(figures))
            + "\n")


def results_index(root: Path, manifests: list[CampaignManifest]) -> str:
    from ..campaigns.freeze import verify_frozen
    frozen = []
    for directory in sorted((root / "results" / "campaigns").glob("*")):
        if directory.is_dir():
            manifest, _ = verify_frozen(directory)
            frozen.append(manifest)
    rows = ["# TADR Benchmark Results", "", "## Campaign registry", "",
            "| Campaign | Target | Algorithm | Checks | Date | Reproducibility | Report |",
            "| --- | --- | --- | --- | --- | --- | --- |"]
    for manifest in frozen:
        rows.append(f"| {manifest.campaign_id} | {manifest.target_package_version} | "
                    f"{manifest.target_algorithm_version} | {len(manifest.planned_scope.check_ids)} declared | "
                    f"{manifest.frozen_date} | Proprietary target; artifact fingerprinted | "
                    f"[Report](results/campaigns/{manifest.campaign_id.lower()}/REPORT.md) |")
    frozen_ids = {item.campaign_id for item in frozen}
    for manifest in sorted(manifests, key=lambda item: item.campaign_id):
        if manifest.campaign_id not in frozen_ids:
            provenance = ("Proprietary target; artifact fingerprinted" if manifest.target_installation_artifact_sha256
                          else "Proprietary target; artifact pending")
            rows.append(f"| {manifest.campaign_id} | {manifest.target_package_version} (planned) | "
                        f"{manifest.target_algorithm_version} | planned scope only | Not run | {provenance} | Not available |")
    rows.extend(["", "## Core Alpha — ALPHA_BENCHMARK_V1", ""])
    if "ALPHA_BENCHMARK_V1" not in frozen_ids:
        rows.extend(["**PLANNED / NOT YET RUN.** No benchmark measurements or figures have been published.", "",
                     "The planned scope covers Check Set A, clean controls, boundary behavior, scores, "
                     "hard gates, determinism, bounded sampling, runtime, throughput and peak RSS.", ""])
    else:
        rows.extend(["See the frozen report in the campaign registry for methodology, tables, figures and limitations.", ""])
    rows.extend(["## Future campaigns", "",
                 "Complete Algorithm v1 (`TADR_BENCHMARK_V1`), optimized Algorithm v1 "
                 "(`TADR_BENCHMARK_V1_FINAL_RESULTS`) and future Algorithm versions will receive separate "
                 "registry entries when frozen artifacts exist. No results are implied by this roadmap.", "",
                 "## Cross-version comparison", "",
                 "Comparisons require at least two frozen campaigns and an explicit compatibility assessment. "
                 "Report the common scenario set, detection/Finding changes, score and hard-gate changes, "
                 "sampling fidelity, newly supported checks and regressions. Runtime/RSS percentage changes "
                 "require an approved equivalent environment class and measurement protocol.", ""])
    return "\n".join(rows)

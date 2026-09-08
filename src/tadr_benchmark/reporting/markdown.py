from pathlib import Path

from ..models import CampaignManifest, CampaignSummary


def campaign_report(manifest: CampaignManifest, summary: CampaignSummary) -> str:
    rows = ["| Scenario / variant | Runs | Runtime median (s) | MAD (s) | Peak RSS median (bytes) | Deterministic |",
            "| --- | ---: | ---: | ---: | ---: | --- |"]
    for group in summary.groups:
        rows.append(f"| {group.scenario_id} / {group.analysis_variant} | {group.measured_runs} | "
                    f"{group.runtime_median_seconds:.6g} | {group.runtime_mad_seconds:.6g} | "
                    f"{group.peak_rss_median_bytes:.6g} | {group.deterministic} |")
    return (f"# {manifest.campaign_id}\n\n"
            f"Target: `{manifest.target_name}` `{manifest.target_package_version}` at "
            f"`{manifest.target_git_commit}`. Algorithm `{manifest.target_algorithm_version}`, "
            f"profile `{manifest.target_threshold_profile}`, bundle `{manifest.target_bundle_protocol}`, "
            f"baseline `{manifest.target_baseline_revision}`.\n\n"
            f"Reproducibility: `{manifest.reproducibility_status}`. Run data SHA-256: "
            f"`{summary.run_data_sha256}`.\n\n"
            "## Methodology and scenario matrix\n\n"
            "The frozen manifest, scenario snapshots and execution plan define the complete experiment. "
            "Ground truth precedes target execution. See [methodology](../../../docs/methodology.md).\n\n"
            "## Detection, negative controls and boundary behavior\n\n"
            "See [summary table](tables/summary.csv) for matched/missed expectations, absent violations "
            "and unexpected Findings. Raw records retain each outcome; counts across repetitions "
            "are not independent samples or calibrated precision estimates.\n\n"
            "## Score behavior, hard gates and suppression\n\n"
            "The table retains score ranges. Each raw record retains risks, ordered Findings, gates "
            "and remediations. Suppressed Findings cannot be reconstructed from final reports.\n\n"
            "## Determinism, runtime, throughput and peak RSS\n\n"
            + "\n".join(rows) + ("\n\n![Runtime](figures/runtime.svg)\n\n" if summary.groups else "\n\nNo successful performance measurements are available.\n\n") +
            "Warmups are retained in runs.jsonl and excluded from aggregates. MAD is the median "
            "absolute deviation. Canonical report disagreement is a determinism failure.\n\n"
            "## Sampling fidelity and scalability\n\n"
            "Variants and scale points are explicit in the manifest. This summary does not infer "
            "full-versus-sampled fidelity or scaling behavior from unrelated scenarios.\n\n"
            "## Failure cases and limitations\n\n"
            f"Terminal coverage (including warmups): {summary.successful_runs} successful reports; "
            f"{summary.adverse_target_outcomes} adverse target outcomes retained in failures.jsonl. "
            "Failed analyses contribute no invented scores or performance values.\n\n"
            "Unexpected outcomes remain in the raw records. Synthetic cases cannot establish "
            "real-world prevalence, model quality or production guarantees. Sampled RSS can miss "
            "short peaks. Review outcomes before drawing scientific conclusions.\n\n"
            "## Reproduction\n\n"
            "Use exact benchmark and target revisions, dependency versions in environment.json, "
            "scenario snapshots and run_specs.json. Verify checksums before analysis. "
            "The bootstrap provides artifact verification; campaign execution is a later implementation.\n")


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
                    f"{manifest.frozen_date} | {manifest.reproducibility_status} | "
                    f"[Report](results/campaigns/{manifest.campaign_id.lower()}/REPORT.md) |")
    frozen_ids = {item.campaign_id for item in frozen}
    for manifest in sorted(manifests, key=lambda item: item.campaign_id):
        if manifest.campaign_id not in frozen_ids:
            rows.append(f"| {manifest.campaign_id} | {manifest.target_package_version} (planned) | "
                        f"{manifest.target_algorithm_version} | planned scope only | Not run | Unverified | Not available |")
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

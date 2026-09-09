"""Deterministic campaign-bound snapshot of the measurement contract."""

from ..models import CampaignManifest
from ..serialization import canonical_bytes


def protocol_bytes(manifest: CampaignManifest) -> bytes:
    policy = {"benchmark_protocol_version": manifest.benchmark_protocol_version,
        "result_schema_version": manifest.result_schema_version, "scenario_set_version": manifest.scenario_set_version,
        "benchmark_git_commit": manifest.benchmark_git_commit, "benchmark_package_version": manifest.benchmark_package_version,
        "execution_groups": [g.model_dump(mode="json") for g in manifest.execution_groups],
        "repeat_policy": manifest.repeat_policy.model_dump(mode="json") if manifest.repeat_policy else None,
        "instrumentation_policy": manifest.instrumentation_policy.model_dump(mode="json") if manifest.instrumentation_policy else None,
        "contexts": [c.model_dump(mode="json") for c in manifest.determinism_cases]}
    return (f"# {manifest.campaign_id} protocol\n\n"
        "Each invocation uses a fresh process. Requested hash seed, timezone, Decimal precision/rounding and four Polars threads "
        "are established and verified before target import. Linux timezone acknowledgement requires tzset.\n\n"
        "Runtime is perf_counter_ns immediately around public tadr.analyze only. Source reads, profiling, checks and scoring "
        "inside that call are included. Generation, external hashes, startup/imports, report encoding/persistence, evaluation, "
        "diagnostics and plotting are excluded. Startup-ready latency is a separate diagnostic.\n\n"
        "The headline peak_rss_bytes is the absolute maximum sampled sum of worker and recursively discovered live-descendant RSS. "
        "The supervisor is excluded. A sample precedes the analyze barrier and a final sample is acknowledged while the worker "
        "remains alive, before canonical report encoding. Requested interval is 10 ms; actual sample count, maximum gap, baseline, "
        "discovery failures and completeness remain visible. Baseline subtraction is only an optional incremental diagnostic. "
        "The 8 GiB sampled guardian is an abort threshold, not a hard memory cap. Short-lived peaks can be missed.\n\n"
        "Sources are deterministically generated and validated against recipe, logical and exact source hashes before reuse. "
        "Filesystem cache state is recently prepared/uncontrolled; no cold-cache claim is made.\n\n"
        "Every RunSpec has one selected scientific terminal outcome. Immutable attempt history retains infrastructure failures "
        "and explicit resolution receipts. Only resolved infrastructure faults permit retries; the first valid report, target "
        "rejection/analysis failure, timeout or resource termination is final. No outcome is chosen for favorable time, memory or score. "
        "Unresolved infrastructure blocks freeze. Operational counts never enter scientific denominators.\n\n"
        "Independent physical and normative labels precede execution. Fixed subject opportunities and severity cutoffs are evaluated "
        "separately by track, check, stratum and format. Scientific detection queries use standard-context measured repeat zero. "
        "Scale/sampling arms and repeats do not inflate primary correctness support. Undefined metrics remain null. Failed outcomes "
        "remain in completion coverage and failure tables without invented scores or successful performance values.\n\n"
        "Finding TP/FP/FN/TN require a successful canonical TADRReport. Without a report, evaluation is UNEVALUABLE; "
        "no failure becomes a negative prediction. conditional_recall=TP/(TP+FN), conditional_precision=TP/(TP+FP), "
        "and conditional_fpr=FP/(FP+TN) use evaluable opportunities only. Each rate retains its numerator/denominator "
        "and accompanies planned/evaluable/unevaluable opportunity support, successful-report coverage and selected target "
        "failure counts by category. Coverage is evaluable/planned opportunities, with positive/negative support separate. "
        "end_to_end_detection_yield=detected positive physical opportunities/all planned positive physical opportunities, "
        "including those without reports. This descriptive pipeline metric is not recall or sensitivity. "
        "Incomplete working queries retain pending reports; freeze still requires complete selected outcomes. "
        "Warmups, repeats and resolved infrastructure attempts do not inflate these scientific denominators.\n\n"
        "entity.cross_split_exposure contributes one physical opportunity per scenario, defect ID and entity subject. "
        "Either final split.group_split_recommended or split.group_leakage_risk on that subject detects it, at most once; "
        "mapped detector identities remain diagnostic detail. Normative expected/absent Findings remain check-specific. "
        "A strong random-split report containing both warnings passes physical detection but fails normative conformance "
        "and the separately preregistered suppression opportunity. Physical, normative and suppression denominators remain separate. "
        "The scenario_matrix opportunity_frames snapshot records the predeclared mapping.\n\n"
        "Exact original report bytes and hashes determine determinism; byte mismatches remain failures of deterministic agreement. "
        "String-equivalent preregistered CSV/Parquet pairs use exact comparison. Native scale projection requires equivalent intended "
        "values/nulls, inferred types, task and selected population/mode, excluding only source-typed top-value encodings. "
        "The raw difference is always retained. Longitudinal eligibility guards remain separate.\n\n"
        "Sampling comparisons use the paired full reference and HEAD_STRIDE_V1 arm: both empty Finding sets have Jaccard one; "
        "severity without common Findings is undefined. Auxiliary public-bundle calls are separate and untimed, expose allowlisted "
        "counts only, and must agree with primary profile/mode/sample ratio. Missing primitives are null with a reason.\n\n"
        "Three measured performance repeats use median, minimum, maximum and unscaled MAD. The two-run 5M policy retains both "
        "values and descriptive median/range with a weak-evidence flag. No inferential significance tests or population accuracy "
        "claims are supported by this purposive synthetic corpus. Warmups stay labeled and outside measured summaries.\n\n"
        "The frozen scenario, expectations, dataset and run-plan snapshots bind the complete construction and task protocol. "
        "The exact benchmark revision binds the independent generators/evaluators.\n\n"
        "```json\n" + canonical_bytes(policy).decode("utf-8") + "```\n").encode("utf-8")

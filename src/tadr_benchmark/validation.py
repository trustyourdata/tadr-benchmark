"""Relational validation in addition to strict individual record schemas."""

from itertools import product
from pathlib import Path

from .campaigns.loader import load_campaign, load_scenario
from .evaluation.detection import evaluate
from .models import (CampaignManifest, EnvironmentInfo, FindingExpectation, GroundTruth,
                     RunResult, RunSpec, ScenarioSpec, TargetMetadata)
from .companions import OutcomeAccounting, RunFailure
from .serialization import canonical_bytes, sha256


def validate_scenarios(manifest: CampaignManifest, scenarios: list[ScenarioSpec]) -> None:
    ids = [scenario.scenario_id for scenario in scenarios]
    if len(ids) != len(set(ids)) or set(ids) != set(manifest.scenario_ids):
        raise ValueError("scenario inventory differs from campaign")
    for scenario in scenarios:
        if (scenario.task_type not in manifest.task_types or scenario.source_format not in manifest.formats
                or scenario.row_count not in manifest.scale_matrix):
            raise ValueError("scenario outside declared campaign matrix")


def planned_runs(manifest: CampaignManifest, scenarios: list[ScenarioSpec]) -> list[RunSpec]:
    if manifest.status == "planned":
        raise ValueError("planned campaigns are not executable")
    return expand_run_plan(manifest, scenarios)


def expand_run_plan(manifest: CampaignManifest, scenarios: list[ScenarioSpec]) -> list[RunSpec]:
    """Pure finite plan expansion, including design validation of PLANNED inputs.

    Groups declare the intended cells; no omitted global Cartesian product is
    implied. Every scenario must be covered. Repeated scenario/variant/context
    cells across groups are errors even if their repeat counts differ.
    """
    validate_scenarios(manifest, scenarios)
    from .models import ExecutionGroup, ScenarioSelector
    if not manifest.scenario_ids:
        return []
    groups = manifest.execution_groups
    if not groups:
        if not (manifest.repeat_policy and manifest.instrumentation_policy):
            raise ValueError("run expansion requires execution policies")
        groups = [ExecutionGroup(group_id="default", selector=ScenarioSelector(include_ids=manifest.scenario_ids),
                                 variant_ids=[v.variant_id for v in manifest.analysis_variants],
                                 context_ids=[c.case_id for c in manifest.determinism_cases],
                                 repeat_policy=manifest.repeat_policy,
                                 instrumentation_policy=manifest.instrumentation_policy)]
    variants = {v.variant_id: v for v in manifest.analysis_variants}
    contexts = {c.case_id: c for c in manifest.determinism_cases}
    inventory = set(manifest.scenario_ids)
    cells, covered = set(), set()
    runs = []
    for group in groups:
        selector = group.selector
        if (set(group.variant_ids)-variants.keys() or set(group.context_ids)-contexts.keys()
                or (set(selector.include_ids) | set(selector.exclude_ids))-inventory):
            raise ValueError("execution group references an unknown scenario/variant/context")
        if any(not any(s.startswith(prefix) for s in inventory) for prefix in selector.include_prefixes):
            raise ValueError("execution group prefix selects no scenarios")
        included = {s for s in inventory if s in selector.include_ids or
                    any(s.startswith(p) for p in selector.include_prefixes)}
        if set(selector.exclude_ids)-included:
            raise ValueError("execution group excludes an unselected scenario")
        selected = included-set(selector.exclude_ids)
        if not selected:
            raise ValueError("empty execution group")
        covered.update(selected)
        for scenario in sorted((s for s in scenarios if s.scenario_id in selected), key=lambda s: s.scenario_id):
            for variant_id, context_id in product(sorted(group.variant_ids), sorted(group.context_ids)):
                variant, case = variants[variant_id], contexts[context_id]
                cell = (scenario.scenario_id, variant.variant_id, case.case_id)
                if cell in cells:
                    raise ValueError("overlapping execution-group cell")
                cells.add(cell)
                for phase, count in (("warmup", group.repeat_policy.warmup_runs),
                                     ("measurement", group.repeat_policy.measurement_runs)):
                    for index in range(count):
                        identity = [manifest.campaign_id, scenario.scenario_id, scenario.scenario_version,
                                    variant.variant_id, case.case_id, phase, index]
                        runs.append(RunSpec(
                            campaign_id=manifest.campaign_id, scenario_id=scenario.scenario_id,
                            scenario_version=scenario.scenario_version,
                            scenario_sha256=sha256(canonical_bytes(scenario)),
                            run_id="run-" + sha256(canonical_bytes(identity)), repeat_index=index,
                            phase=phase, determinism_case_id=case.case_id, determinism_context=case,
                            analysis_variant=variant.variant_id, constraints=variant.constraints,
                            execution_group_id=group.group_id if manifest.execution_groups else None,
                            instrumentation_policy=group.instrumentation_policy))
    if covered != inventory:
        raise ValueError("uncovered scenario cells in execution groups")
    if {c[1] for c in cells} != variants.keys() or {c[2] for c in cells} != contexts.keys():
        raise ValueError("uncovered variant/context axis")
    if manifest.campaign_id == "ALPHA_BENCHMARK_V1":
        from .scenarios.plan import validate_alpha_cells
        validate_alpha_cells(manifest, scenarios, runs)
    return sorted(runs, key=lambda item: item.run_id)


def account_outcomes(plan: list[RunSpec], runs: list[RunResult],
                     failures: list[RunFailure]) -> OutcomeAccounting:
    expected = {r.run_id for r in plan}
    ids = [r.run_id for r in [*runs, *failures]]
    if len(expected) != len(plan) or len(ids) != len(set(ids)) or set(ids)-expected:
        raise ValueError("terminal runs are duplicated or unexpected")
    infrastructure = sum(f.failure_kind == "infrastructure" or
                         f.adjudication == "infrastructure_failure" for f in failures)
    adverse = sum(f.adjudication == "valid_target_outcome" for f in failures)
    return OutcomeAccounting(planned=len(plan), successful=len(runs), adverse_target_outcomes=adverse,
                             infrastructure_failures=infrastructure,
                             unresolved=len(expected)-len(runs)-adverse-infrastructure)


def run_ground_truth(scenario: ScenarioSpec, variant_id: str) -> GroundTruth:
    if scenario.generator != "alpha.tabular":
        return scenario.ground_truth()
    from .scenarios.expectations import expectations_for
    variants = {v.variant_id: v for v in expectations_for(scenario).normative}
    if variant_id not in variants:
        raise ValueError("missing normative annotation for analysis variant")
    variant = variants[variant_id]
    return GroundTruth(expected_findings=[FindingExpectation(id_pattern=f.check_id+"::*", subject=f.subject)
                                         for f in variant.findings],
                       expected_absent_findings=[FindingExpectation(id_pattern=c+"::*") for c in variant.absent_check_ids],
                       expected_affected_columns=scenario.expected_affected_columns,
                       expected_gate_behavior="present" if variant.gates else "none", rationale=scenario.rationale)


def validate_completed(manifest: CampaignManifest, scenarios: list[ScenarioSpec],
                       runs: list[RunResult], environments: dict[str, EnvironmentInfo],
                       failures: list[RunFailure] | None = None) -> OutcomeAccounting:
    failures = failures or []
    expected = {run.run_id: run for run in planned_runs(manifest, scenarios)}
    accounting = account_outcomes(list(expected.values()), runs, failures)
    if accounting.infrastructure_failures:
        raise ValueError("infrastructure failure blocks campaign freeze")
    if accounting.unresolved:
        raise ValueError("requested runs are missing, duplicated or unexpected")
    if manifest.benchmark_git_commit is None:
        raise ValueError("completed outcomes require a resolved benchmark revision")
    outcomes = [*runs, *failures]
    scenario_map = {scenario.scenario_id: scenario for scenario in scenarios}
    for scenario_id in scenario_map:
        if len({(run.logical_dataset_sha256, run.source_file_sha256)
                for run in outcomes if run.scenario_id == scenario_id}) != 1:
            raise ValueError("scenario repeats/variants must use the same generated dataset")
    if set(environments) != {run.environment_id for run in outcomes}:
        raise ValueError("environment inventory differs from run records")
    for key, env in environments.items():
        if key != env.environment_id or env.python_version != manifest.python_version:
            raise ValueError("environment identity or Python version mismatch")
        if manifest.campaign_id == "ALPHA_BENCHMARK_V1" and (env.os != "Linux" or env.architecture != "x86_64"):
            raise ValueError("Alpha requires its approved Linux x86_64 execution environment")
        for package, version in (("tadr-benchmark", manifest.benchmark_package_version),
                                 ("tadr-core", manifest.target_package_version)):
            if env.dependency_versions.get(package) != version:
                raise ValueError("environment package provenance mismatch")
    for run in outcomes:
        spec = expected[run.run_id]
        for field in RunSpec.model_fields:
            if getattr(run, field) != getattr(spec, field):
                raise ValueError(f"run differs from execution plan: {field}")
        for field in (*TargetMetadata.model_fields, "benchmark_git_commit", "benchmark_package_version",
                      "benchmark_protocol_version", "result_schema_version"):
            if getattr(run, field) != getattr(manifest, field):
                raise ValueError(f"run provenance differs from campaign: {field}")
        scenario = scenario_map[run.scenario_id]
        if isinstance(run, RunFailure):
            if run.failure_kind == "timeout" and run.policy_limit != spec.instrumentation_policy.timeout_seconds:
                raise ValueError("timeout limit differs from declared instrumentation policy")
            if manifest.campaign_id == "ALPHA_BENCHMARK_V1" and run.failure_kind == "resource_abort" and run.policy_limit != 8*1024**3:
                raise ValueError("resource abort differs from approved Alpha limit")
            continue
        if scenario.scenario_id.startswith("sampling."):
            from .report_precision import validate_sampling_observation
            validate_sampling_observation(run.analysis_variant, run.analysis_mode, run.sample_ratio)
        for field in ("task_type", "source_format", "row_count", "column_count"):
            if getattr(run, field) != getattr(scenario, field):
                raise ValueError(f"run differs from scenario: {field}")
        truth = run_ground_truth(scenario, run.analysis_variant)
        if run.expected_finding_ids_or_patterns != truth.expected_findings:
            raise ValueError("run ground truth differs from scenario")
        if run.detection_outcome != evaluate(truth, run.finding_ids,
                                            run.finding_subjects, run.hard_gates):
            raise ValueError("stored evaluation differs from independent ground truth")
    return accounting


def validate_historical_scenarios(root: Path, scenarios: list[ScenarioSpec]) -> None:
    historical = [ScenarioSpec.model_validate_json(path.read_bytes()) for path in
                  sorted((root / "results" / "campaigns").glob("*/scenarios/*.json"))]
    identities = {}
    for scenario in historical + scenarios:
        key = (scenario.scenario_id, scenario.scenario_version)
        content = canonical_bytes(scenario)
        if key in identities and identities[key] != content:
            raise ValueError("historical scenario version has changed")
        identities[key] = content


def validate_repository(root: Path) -> list[CampaignManifest]:
    def definitions(directory, recursive):
        paths = directory.rglob("*") if recursive else directory.glob("*")
        return sorted(path for path in paths if path.is_file() and path.suffix in {".yaml", ".yml", ".json"})

    from .scenarios.families import load_family_scenarios
    scenarios = [load_scenario(path) for path in definitions(root / "scenarios", True)
                 if path.parent.name != "families"]
    scenarios.extend(load_family_scenarios(root))
    if len({item.scenario_id for item in scenarios}) != len(scenarios):
        raise ValueError("duplicate active scenario ID")
    manifests = [load_campaign(path) for path in definitions(root / "campaigns", False)]
    if len({item.campaign_id.lower() for item in manifests}) != len(manifests):
        raise ValueError("duplicate campaign directory identity")
    for manifest in manifests:
        selected = [item for item in scenarios if item.scenario_id in manifest.scenario_ids]
        validate_scenarios(manifest, selected)
        expand_run_plan(manifest, selected)
    from .campaigns.freeze import verify_frozen
    for directory in sorted((root / "results" / "campaigns").glob("*")):
        if directory.is_dir():
            verify_frozen(directory)
    validate_historical_scenarios(root, scenarios)
    return manifests

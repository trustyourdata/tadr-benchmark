"""Relational validation in addition to strict individual record schemas."""

from pathlib import Path

from .campaigns.loader import load_campaign, load_scenario
from .evaluation.detection import evaluate
from .models import CampaignManifest, EnvironmentInfo, RunResult, RunSpec, ScenarioSpec, TargetMetadata
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
    validate_scenarios(manifest, scenarios)
    if manifest.status == "planned":
        raise ValueError("planned campaigns are not executable")
    runs = []
    for scenario in sorted(scenarios, key=lambda item: item.scenario_id):
        for variant in sorted(manifest.analysis_variants, key=lambda item: item.variant_id):
            for case in sorted(manifest.determinism_cases, key=lambda item: item.case_id):
                for phase, count in (("warmup", manifest.repeat_policy.warmup_runs),
                                     ("measurement", manifest.repeat_policy.measurement_runs)):
                    for index in range(count):
                        identity = [manifest.campaign_id, scenario.scenario_id, scenario.scenario_version,
                                    variant.variant_id, case.case_id, phase, index]
                        runs.append(RunSpec(
                            campaign_id=manifest.campaign_id, scenario_id=scenario.scenario_id,
                            scenario_version=scenario.scenario_version,
                            scenario_sha256=sha256(canonical_bytes(scenario)),
                            run_id="run-" + sha256(canonical_bytes(identity)), repeat_index=index,
                            phase=phase, determinism_case_id=case.case_id, determinism_context=case,
                            analysis_variant=variant.variant_id, constraints=variant.constraints))
    return sorted(runs, key=lambda item: item.run_id)


def validate_completed(manifest: CampaignManifest, scenarios: list[ScenarioSpec],
                       runs: list[RunResult], environments: dict[str, EnvironmentInfo]) -> None:
    expected = {run.run_id: run for run in planned_runs(manifest, scenarios)}
    observed = {run.run_id: run for run in runs}
    if len(observed) != len(runs) or set(observed) != set(expected):
        raise ValueError("requested runs are missing, duplicated or unexpected")
    scenario_map = {scenario.scenario_id: scenario for scenario in scenarios}
    for scenario_id in scenario_map:
        if len({run.dataset_sha256 for run in runs if run.scenario_id == scenario_id}) != 1:
            raise ValueError("scenario repeats/variants must use the same generated dataset")
    if set(environments) != {run.environment_id for run in runs}:
        raise ValueError("environment inventory differs from run records")
    for key, env in environments.items():
        if key != env.environment_id or env.python_version != manifest.python_version:
            raise ValueError("environment identity or Python version mismatch")
        for package, version in (("tadr-benchmark", manifest.benchmark_package_version),
                                 ("tadr-core", manifest.target_package_version)):
            if env.dependency_versions.get(package) != version:
                raise ValueError("environment package provenance mismatch")
    for run in runs:
        spec = expected[run.run_id]
        for field in RunSpec.model_fields:
            if getattr(run, field) != getattr(spec, field):
                raise ValueError(f"run differs from execution plan: {field}")
        for field in (*TargetMetadata.model_fields, "benchmark_git_commit", "benchmark_package_version",
                      "benchmark_protocol_version", "result_schema_version", "instrumentation_policy"):
            if getattr(run, field) != getattr(manifest, field):
                raise ValueError(f"run provenance differs from campaign: {field}")
        scenario = scenario_map[run.scenario_id]
        for field in ("task_type", "source_format", "row_count", "column_count"):
            if getattr(run, field) != getattr(scenario, field):
                raise ValueError(f"run differs from scenario: {field}")
        if run.expected_finding_ids_or_patterns != scenario.expected_findings:
            raise ValueError("run ground truth differs from scenario")
        if run.detection_outcome != evaluate(scenario.ground_truth(), run.finding_ids,
                                            run.finding_subjects, run.hard_gates):
            raise ValueError("stored evaluation differs from independent ground truth")


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

    scenarios = [load_scenario(path) for path in definitions(root / "scenarios", True)]
    if len({item.scenario_id for item in scenarios}) != len(scenarios):
        raise ValueError("duplicate active scenario ID")
    manifests = [load_campaign(path) for path in definitions(root / "campaigns", False)]
    if len({item.campaign_id.lower() for item in manifests}) != len(manifests):
        raise ValueError("duplicate campaign directory identity")
    for manifest in manifests:
        selected = [item for item in scenarios if item.scenario_id in manifest.scenario_ids]
        validate_scenarios(manifest, selected)
    from .campaigns.freeze import verify_frozen
    for directory in sorted((root / "results" / "campaigns").glob("*")):
        if directory.is_dir():
            verify_frozen(directory)
    validate_historical_scenarios(root, scenarios)
    return manifests

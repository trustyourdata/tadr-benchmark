"""Explicit finite campaign execution; no implicit retry or publication."""

from pathlib import Path

from ..companions import RunFailure
from ..execution.diagnostics import invoke_diagnostic, load_diagnostic, persist_diagnostic
from ..execution.executor import execute_run
from ..execution.ledger import RunLedger
from ..instrumentation.environment import capture_environment
from ..models import CampaignManifest, RunResult, ScenarioSpec
from ..paths import contained
from ..serialization import canonical_bytes, sha256
from ..validation import planned_runs
from .freeze import resolve_manifest
from .schedule import execution_schedule


def run_campaign(root: Path, manifest: CampaignManifest, scenarios: list[ScenarioSpec], *, installation_artifact: Path | None = None):
    """Run the explicitly requested READY plan; never retries infrastructure or freezes.

    An infrastructure outcome stops further execution. The caller must diagnose
    and explicitly resolve it before a subsequent invocation can retry that cell.
    """
    manifest = resolve_manifest(root, manifest)
    specs = planned_runs(manifest, scenarios)
    schedule = execution_schedule(manifest, scenarios, specs)
    environment = capture_environment()
    if environment.python_version != manifest.python_version:
        raise ValueError("execution Python differs from manifest")
    if manifest.campaign_id == "ALPHA_BENCHMARK_V1" and (environment.os != "Linux" or environment.architecture != "x86_64"):
        raise ValueError("Alpha requires the approved Linux execution host")
    for name, version in (("tadr-benchmark", manifest.benchmark_package_version), ("tadr-core", manifest.target_package_version)):
        if environment.dependency_versions.get(name) != version:
            raise ValueError("execution package provenance differs")
    directory = contained(root, ".work/campaigns/" + manifest.campaign_id.lower())
    binding = {"manifest": manifest.model_dump(mode="json"), "environment": environment.model_dump(mode="json"),
               "scenarios_sha256": sha256(canonical_bytes([s.model_dump(mode="json") for s in sorted(scenarios, key=lambda s: s.scenario_id)]))}
    by_id = {s.scenario_id: s for s in scenarios}
    with RunLedger(directory / "ledger", specs, binding) as ledger:
        for spec in schedule:
            scenario = by_id[spec.scenario_id]
            outcome = execute_run(root, manifest, spec, scenario, environment, ledger, installation_artifact=installation_artifact)
            if isinstance(outcome, RunFailure) and outcome.failure_kind == "infrastructure":
                return ledger.snapshot()
            if isinstance(outcome, RunResult) and spec.scenario_id.startswith("sampling.") and (
                    spec.phase == "measurement" and spec.repeat_index == 0 and spec.determinism_case_id == "standard"):
                path = directory / "diagnostics" / (spec.run_id+".json")
                selected = next(a for a in ledger.snapshot() if a.run_id == spec.run_id and a.selected_as_final_outcome)
                report = (directory / "ledger" / selected.attempt_id / "report.json").read_bytes()
                if path.exists():
                    load_diagnostic(path, outcome, report)
                else:
                    source = contained(root, f".work/datasets/{scenario.scenario_id}.parquet")
                    diagnostic = invoke_diagnostic(outcome, source,
                        {"task_type": scenario.task_type, **scenario.task_parameters}, scenario.generator_parameters["case"],
                        report, installation_artifact=installation_artifact)
                    persist_diagnostic(path, diagnostic)
        return ledger.snapshot()

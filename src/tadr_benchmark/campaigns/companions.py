"""Relational validation of authoritative labels and observation companions."""

from ..companions import (DatasetIdentity, DiagnosticRecord, InstrumentationRecord,
                          RunFailure, ScenarioExpectations)
from ..models import CampaignManifest, RunResult, ScenarioSpec, TargetMetadata
from ..serialization import canonical_bytes, sha256


def validate_companions(manifest: CampaignManifest, scenarios: list[ScenarioSpec],
                        runs: list[RunResult], failures: list[RunFailure],
                        expectations: list[ScenarioExpectations], datasets: list[DatasetIdentity],
                        instrumentation: list[InstrumentationRecord], diagnostics: list[DiagnosticRecord]) -> None:
    required = manifest.campaign_id == "ALPHA_BENCHMARK_V1" or any(
        (expectations, datasets, instrumentation, diagnostics))
    if not required:
        return  # Tiny generic harness fixtures do not declare Alpha companions.

    def inventory(items, field, expected):
        indexed = {getattr(item, field): item for item in items}
        if len(indexed) != len(items) or set(indexed) != set(expected):
            raise ValueError("companion inventory differs: "+field)
        return indexed

    scenario_map = {s.scenario_id: s for s in scenarios}
    labels = inventory(expectations, "scenario_id", scenario_map)
    sources = inventory(datasets, "scenario_id", scenario_map)
    outcomes = [*runs, *failures]
    monitors = inventory(instrumentation, "run_id", [r.run_id for r in outcomes])
    for sid, scenario in scenario_map.items():
        expected_hash = sha256(canonical_bytes(scenario))
        label, dataset = labels[sid], sources[sid]
        for record in (label, dataset):
            if record.scenario_sha256 != expected_hash or record.scenario_version != scenario.scenario_version:
                raise ValueError("companion scenario provenance differs")
        if dataset.row_count != scenario.row_count or len(dataset.logical_schema) != scenario.column_count:
            raise ValueError("dataset dimensions differ from scenario")
        if (label.physical.row_count != scenario.row_count or
                label.physical.column_names != [c.name for c in dataset.logical_schema]):
            raise ValueError("physical ledger differs from dataset schema/dimensions")
        physical_format = "csv" if dataset.writer_policy.representation == "csv" else "parquet"
        if physical_format != scenario.source_format:
            raise ValueError("source representation differs from scenario format")
        if scenario.generator == "alpha.tabular":
            from ..scenarios.expectations import expectations_for
            from ..scenarios.recipe import Recipe
            from ..generators.writers import logical_schema
            recipe = Recipe.model_validate(scenario.generator_parameters)
            if label != expectations_for(scenario):
                raise ValueError("frozen labels differ from independent definitions")
            if dataset.logical_schema != logical_schema(recipe) or dataset.writer_policy.representation != recipe.representation:
                raise ValueError("dataset logical schema or representation differs")
    for run in outcomes:
        source = sources[run.scenario_id]
        if (run.logical_dataset_sha256, run.source_file_sha256) != (
                source.logical_dataset_sha256, source.source_file_sha256):
            raise ValueError("run dataset identity differs from dataset manifest")
        monitor = monitors[run.run_id]
        success = isinstance(run, RunResult)
        if monitor.terminal_state != ("success" if success else "failure"):
            raise ValueError("instrumentation terminal state differs")
        if not monitor.effective_context_confirmed or monitor.polars_max_threads != 4:
            raise ValueError("execution context was not validated")
        if success and not (monitor.analysis_start_acknowledged and monitor.analysis_end_acknowledged
                            and monitor.sample_count and monitor.baseline_rss_bytes is not None
                            and monitor.maximum_sample_gap_seconds is not None
                            and monitor.unavailable_reason is None):
            raise ValueError("successful timing requires complete instrumentation")
        if manifest.campaign_id == "ALPHA_BENCHMARK_V1" and (
                monitor.effective_context != run.determinism_context or monitor.timezone_verification_method != "tzset"
                or monitor.requested_interval_seconds != 0.01 or monitor.rss_abort_limit_bytes != 8*1024**3
                or monitor.monitor_completeness != "complete" or monitor.descendant_discovery_failed):
            raise ValueError("Alpha instrumentation protocol acknowledgement is incomplete")
    # Failed primary analysis has a terminal failure instead of invented bundle
    # diagnostics. Every successful standard repeat-0 sampling arm needs a companion.
    primaries = {r.run_id: r for r in runs if r.scenario_id.startswith("sampling.") and
                 r.phase == "measurement" and r.repeat_index == 0 and r.determinism_case_id == "standard"}
    inventory(diagnostics, "primary_run_id", primaries)
    for diagnostic in diagnostics:
        run = primaries[diagnostic.primary_run_id]
        if diagnostic.primary_report_sha256 != run.canonical_report_sha256:
            raise ValueError("diagnostic primary report hash differs")
        for field in (*TargetMetadata.model_fields, "scenario_id", "scenario_sha256", "benchmark_git_commit",
                      "logical_dataset_sha256", "source_file_sha256", "environment_id", "analysis_variant",
                      "determinism_case_id", "determinism_context", "constraints", "analysis_mode", "sample_ratio"):
            if getattr(diagnostic, field) != getattr(run, field):
                raise ValueError("diagnostic provenance differs from primary run: "+field)
        from ..report_precision import validate_sampling_observation
        validate_sampling_observation(run.analysis_variant, diagnostic.analysis_mode, diagnostic.sample_ratio)

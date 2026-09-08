"""Chronological execution order, independent of canonical RunSpec ordering."""

from ..models import CampaignManifest, RunSpec, ScenarioSpec


_ALPHA_GROUP_RANK = {
    "correctness": 0,
    "sampling_reference": 1,
    "sampling_bounded": 1,
    "determinism_small": 2,
    "determinism_sampled": 3,
    "scale_regular": 4,
    "scale_large": 5,
}
_CONTEXT_RANK = {name: index for index, name in enumerate((
    "standard", "hash_one", "hash_fortytwo", "timezone_berlin", "decimal_low", "decimal_high"))}


def execution_schedule(manifest: CampaignManifest, scenarios: list[ScenarioSpec],
                       specs: list[RunSpec]) -> list[RunSpec]:
    """Reorder a validated plan without changing its objects, identities or binding.

    Alpha pairs ordinary sampling arms and keeps each scale cell contiguous,
    with its warmup before measured repeats. Other campaigns retain their
    existing run-ID traversal until they declare a separate execution policy.
    """
    if len({spec.run_id for spec in specs}) != len(specs):
        raise ValueError("duplicate RunSpec in execution schedule")
    if manifest.campaign_id != "ALPHA_BENCHMARK_V1":
        return sorted(specs, key=lambda spec: spec.run_id)
    if any(spec.execution_group_id not in _ALPHA_GROUP_RANK for spec in specs):
        raise ValueError("unknown Alpha execution group")
    by_id = {scenario.scenario_id: scenario for scenario in scenarios}

    def order(spec):
        group = spec.execution_group_id
        rank = _ALPHA_GROUP_RANK[group]
        phase_repeat = (0 if spec.phase == "warmup" else 1, spec.repeat_index, spec.run_id)
        cell = (spec.scenario_id, spec.analysis_variant, spec.determinism_case_id)
        if group in {"sampling_reference", "sampling_bounded"}:
            arm = 0 if spec.analysis_variant == "full_reference" else 1
            return (rank, spec.scenario_id, arm, spec.determinism_case_id, *phase_repeat)
        if group in {"determinism_small", "determinism_sampled"}:
            return (rank, spec.scenario_id, spec.analysis_variant,
                    _CONTEXT_RANK[spec.determinism_case_id], *phase_repeat)
        if group in {"scale_regular", "scale_large"}:
            scenario = by_id[spec.scenario_id]
            return (rank, scenario.row_count, scenario.column_count, scenario.task_type,
                    scenario.generator_parameters["representation"], *cell, *phase_repeat)
        return (rank, *cell, *phase_repeat)

    return sorted(specs, key=order)

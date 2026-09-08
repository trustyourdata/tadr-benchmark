from pathlib import Path

import pytest
from pydantic import ValidationError

from tadr_benchmark.campaigns.freeze import resolve_manifest
from tadr_benchmark.campaigns.loader import load_campaign
from tadr_benchmark.models import CampaignManifest, ExecutionGroup
from tadr_benchmark.scenarios.families import load_family_scenarios
from tadr_benchmark.validation import expand_run_plan

ROOT = Path(__file__).parents[1]


def group(campaign, name, ids, variant="full_reference", context="standard"):
    return ExecutionGroup(group_id=name, selector={"include_ids": ids}, variant_ids=[variant],
                          context_ids=[context], repeat_policy=campaign.repeat_policy,
                          instrumentation_policy=campaign.instrumentation_policy)


def test_approved_alpha_plan_is_finite_exact_and_order_independent():
    campaign = load_campaign(ROOT / "campaigns/ALPHA_BENCHMARK_V1.yaml")
    scenarios = load_family_scenarios(ROOT)
    plan = expand_run_plan(campaign, scenarios)
    assert len(plan) == len({r.run_id for r in plan}) == 578
    assert sum(r.phase == "warmup" for r in plan) == 13
    from collections import Counter
    assert Counter(r.execution_group_id for r in plan) == {
        "correctness": 310, "sampling_reference": 36, "sampling_bounded": 34,
        "determinism_small": 120, "determinism_sampled": 24, "scale_regular": 52, "scale_large": 2}
    altered = CampaignManifest.model_validate({**campaign.model_dump(), "execution_groups": list(reversed(campaign.execution_groups))})
    assert expand_run_plan(altered, list(reversed(scenarios))) == plan
    assert all(r.instrumentation_policy.protocol_version == "1.0" for r in plan)


def test_group_overlap_is_rejected_even_with_different_repeat_counts(campaign, scenario):
    first = group(campaign, "one", [scenario.scenario_id])
    second = ExecutionGroup.model_validate({**first.model_dump(), "group_id": "two",
                                            "repeat_policy": {"warmup_runs": 0, "measurement_runs": 1}})
    manifest = CampaignManifest.model_validate({**campaign.model_dump(), "execution_groups": [first, second]})
    with pytest.raises(ValueError, match="overlapping"):
        expand_run_plan(manifest, [scenario])


@pytest.mark.parametrize("change,match", [
    ({"selector": {"include_ids": ["unknown"]}}, "unknown"),
    ({"selector": {"include_prefixes": ["unknown."]}}, "selects no"),
    ({"selector": {"include_ids": ["fixture.clean"], "exclude_ids": ["fixture.clean"]}}, "empty"),
    ({"variant_ids": ["unknown"]}, "unknown"), ({"context_ids": ["unknown"]}, "unknown")])
def test_invalid_group_references(campaign, scenario, change, match):
    g = group(campaign, "one", [scenario.scenario_id])
    g = ExecutionGroup.model_validate({**g.model_dump(), **change})
    manifest = CampaignManifest.model_validate({**campaign.model_dump(), "execution_groups": [g]})
    with pytest.raises(ValueError, match=match):
        expand_run_plan(manifest, [scenario])


def test_uncovered_scenario_is_rejected(campaign, scenario):
    other = type(scenario).model_validate({**scenario.model_dump(), "scenario_id": "fixture.other"})
    manifest = CampaignManifest.model_validate({**campaign.model_dump(),
        "scenario_ids": [scenario.scenario_id, other.scenario_id],
        "execution_groups": [group(campaign, "one", [scenario.scenario_id])]})
    with pytest.raises(ValueError, match="uncovered"):
        expand_run_plan(manifest, [scenario, other])


def test_uncovered_context_is_rejected(campaign, scenario):
    contexts = campaign.determinism_cases + [campaign.determinism_cases[0].model_copy(update={"case_id": "unused"})]
    manifest = CampaignManifest.model_validate({**campaign.model_dump(), "determinism_cases": contexts,
        "execution_groups": [group(campaign, "one", [scenario.scenario_id])]})
    with pytest.raises(ValueError, match="uncovered"):
        expand_run_plan(manifest, [scenario])


def test_source_revision_is_null_and_resolved_without_source_mutation(campaign, tmp_path, monkeypatch):
    source = CampaignManifest.model_validate({**campaign.model_dump(), "benchmark_git_commit": None})
    from types import SimpleNamespace
    from tadr_benchmark.campaigns import freeze
    answers = iter(["", "a"*40])
    monkeypatch.setattr(freeze.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout=next(answers)))
    resolved = resolve_manifest(tmp_path, source)
    assert resolved.benchmark_git_commit == "a"*40
    assert source.benchmark_git_commit is None
    path = tmp_path / "source.yaml"
    path.write_text(resolved.model_dump_json(), encoding="utf-8")
    with pytest.raises(ValueError, match="unresolved"):
        load_campaign(path)


def test_missing_sampling_arm_is_rejected_even_if_scenario_is_still_covered():
    campaign = load_campaign(ROOT / "campaigns/ALPHA_BENCHMARK_V1.yaml")
    scenarios = load_family_scenarios(ROOT)
    data = campaign.model_dump()
    reference = next(g for g in data["execution_groups"] if g["group_id"] == "sampling_reference")
    reference["selector"]["exclude_ids"].append("sampling.parse.head.n300000.pqstr")
    with pytest.raises(ValueError, match="required Alpha execution cells"):
        expand_run_plan(CampaignManifest.model_validate(data), scenarios)


def test_alpha_cannot_be_ready_on_unprovisioned_host():
    campaign = load_campaign(ROOT / "campaigns/ALPHA_BENCHMARK_V1.yaml")
    with pytest.raises(ValidationError, match="provisioned"):
        CampaignManifest.model_validate({**campaign.model_dump(), "status": "ready",
            "execution_readiness": {**campaign.execution_readiness.model_dump(), "host_provisioned": False}})


def test_initial_versions_reject_unapproved_bumps(campaign):
    for change in ({"benchmark_protocol_version": "1.1"}, {"result_schema_version": "1.1"},
                   {"instrumentation_policy": {**campaign.instrumentation_policy.model_dump(), "protocol_version": "1.1"}}):
        with pytest.raises(ValidationError):
            CampaignManifest.model_validate({**campaign.model_dump(), **change})

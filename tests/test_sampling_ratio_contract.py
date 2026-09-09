from decimal import Decimal, localcontext

import pytest

from test_companions import companions  # shared synthetic companion fixture
from tadr_benchmark.campaigns.companions import validate_companions
from tadr_benchmark.execution.diagnostics import METRICS, diagnostic_record, report_visible_facts
from tadr_benchmark.models import CampaignManifest, RunResult
from tadr_benchmark.report_precision import canonical_report_rate, expected_sampling_observation
from tadr_benchmark.serialization import canonical_bytes, sha256
from tadr_benchmark.validation import planned_runs, validate_completed


@pytest.fixture
def scenario(scenario):
    return scenario.model_copy(update={"scenario_id": "sampling.fixture"})


def test_expected_ratio_uses_pinned_precision_independent_of_decimal_context():
    with localcontext() as context:
        context.prec = 2
        assert expected_sampling_observation("HEAD_STRIDE_V1") == ("sampled", 0.6667)
    assert canonical_report_rate(200000/300000) == Decimal("0.6667")
    assert canonical_report_rate(Decimal("0.12345")) == Decimal("0.1234")
    assert canonical_report_rate(Decimal("0.12355")) == Decimal("0.1236")
    facts = {"analysis_stats": {"sample_ratio": Decimal(2)/3}, "dataset_profile": {}}
    assert report_visible_facts(facts)["analysis_stats"]["sample_ratio"] == expected_sampling_observation("HEAD_STRIDE_V1")[1]


@pytest.mark.parametrize("variant,mode,ratio,passes", [
    ("HEAD_STRIDE_V1", "sampled", 0.6667, True),
    ("full_reference", "full", 1.0, True),
    ("HEAD_STRIDE_V1", "sampled", 0.6666, False),
    ("HEAD_STRIDE_V1", "sampled", 0.6668, False),
    ("HEAD_STRIDE_V1", "sampled", 2/3, False),
    ("HEAD_STRIDE_V1", "sampled", 0.66670001, False),
    ("HEAD_STRIDE_V1", "full", 0.6667, False),
    ("full_reference", "full", 0.9999, False),
])
def test_completed_and_companion_validators_agree(campaign, scenario, completed, environment,
                                                  companions, variant, mode, ratio, passes):
    manifest = CampaignManifest.model_validate({**campaign.model_dump(),
        "analysis_variants": [{"variant_id": variant, "constraints": {}}]})
    runs = [RunResult.model_validate({**old.model_dump(), **spec.model_dump(),
        "analysis_mode": mode, "sample_ratio": ratio})
        for old, spec in zip(completed[0], planned_runs(manifest, [scenario]))]
    companions["instrumentation"] = [m.model_copy(update={"run_id": r.run_id})
        for m, r in zip(companions["instrumentation"], runs)]
    primary = next(r for r in runs if r.phase == "measurement" and r.repeat_index == 0)
    payload = {"analysis_stats": {"analysis_mode": mode, "sample_ratio": ratio},
        "dataset_profile": {"columns": []}, "algorithm_version": primary.target_algorithm_version,
        "threshold_profile": primary.target_threshold_profile, "protocol_version": primary.target_bundle_protocol,
        "metrics": {k: {"value": None, "unavailable_reason": "not_exposed"} for k in METRICS}}
    original = canonical_bytes(payload)
    primary = primary.model_copy(update={"canonical_report_sha256": sha256(original)})
    runs = [primary if r.run_id == primary.run_id else r for r in runs]
    companions["diagnostics"] = [diagnostic_record(primary, original, payload)]
    for check in (lambda: validate_completed(manifest, [scenario], runs, {environment.environment_id: environment}),
                  lambda: validate_companions(manifest, [scenario], runs, [], **companions)):
        if passes:
            check()
        else:
            with pytest.raises(ValueError, match="sampling mode/ratio"):
                check()

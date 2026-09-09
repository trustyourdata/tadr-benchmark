import pytest

from tadr_benchmark.evaluation.metrics import evaluate_frame, evaluate_scenario
from tadr_benchmark.evaluation.opportunities import GROUP_DETECTORS, alpha_opportunities
from tadr_benchmark.scenarios.expectations import expectations_for, make_scenario
from tadr_benchmark.scenarios.recipe import recipe_from_id


def example(split="random", share=2000):
    scenario = make_scenario(recipe_from_id(f"group.{split}.r{share}.n10000.csv"))
    return scenario, alpha_opportunities(scenario, "full_reference"), expectations_for(scenario).normative[0]


def report(detectors, subject="entity:entity_key", severity="HIGH"):
    return {"findings": [{"id": check+"::"+subject, "severity": severity, "confidence": "0.9",
        "metadata": {"check_id": check, "subject_key": subject}} for check in detectors],
        "score_breakdown": {"caps_applied": []}, "readiness_score": 80}


@pytest.mark.parametrize("detectors,tp,fn", [([], 0, 1), ([GROUP_DETECTORS[0]], 1, 0),
    ([GROUP_DETECTORS[1]], 1, 0), (GROUP_DETECTORS, 1, 0)])
def test_entity_physical_opportunity_is_unique_with_or_detection(detectors, tp, fn):
    scenario, frame, labels = example()
    shared = [o for o in frame if o.track == "controlled_condition" and o.physical_defect_id == "entity.cross_split_exposure"]
    assert len(shared) == 1
    assert shared[0].scenario_id == scenario.scenario_id
    assert shared[0].subject == "entity:entity_key"
    observed = evaluate_frame(shared, report(detectors))[0]
    assert (observed.tp, observed.fn) == (tp, fn)
    assert observed.conditional_recall.denominator == 1
    assert observed.mapped_detector_details[shared[0].opportunity_id] == sorted(detectors)


def test_both_detectors_fail_normative_and_suppression_but_have_one_physical_tp():
    _, frame, labels = example()
    outcome = evaluate_scenario(frame, labels, report(GROUP_DETECTORS))
    assert not outcome["normative_conformant"]
    assert outcome["controlled_condition"]["detected_opportunities"] == 1
    assert outcome["controlled_condition"]["positive_opportunities"] == 1
    assert outcome["gates_and_suppression"]["suppression_correctness"] == {
        "numerator": 0, "denominator": 1, "value": 0.0}
    normative = evaluate_frame([o for o in frame if o.track == "normative"], report(GROUP_DETECTORS))
    assert next(m for m in normative if m.check_id == GROUP_DETECTORS[0]).fp == 1


def test_wrong_mapped_detector_is_a_physical_tp_and_normative_failure():
    _, frame, labels = example()
    outcome = evaluate_scenario(frame, labels, report([GROUP_DETECTORS[0]]))
    assert outcome["controlled_condition"]["detected_opportunities"] == 1
    assert not outcome["normative_conformant"]
    assert outcome["gates_and_suppression"]["suppression_correctness"]["value"] == 0


@pytest.mark.parametrize("split,share,detector,severity", [("random", 500, GROUP_DETECTORS[0], "MEDIUM"),
    ("random", 2000, GROUP_DETECTORS[1], "HIGH"), ("time", 2000, GROUP_DETECTORS[0], "HIGH"),
    ("group", 2000, None, "HIGH")])
def test_normative_split_selection_remains_exact(split, share, detector, severity):
    _, frame, labels = example(split, share)
    assert evaluate_scenario(frame, labels, report([detector] if detector else [], severity=severity))["normative_conformant"]


def test_wrong_entity_and_duplicate_physical_identity_are_rejected():
    _, frame, _ = example()
    shared = [o for o in frame if o.physical_defect_id == "entity.cross_split_exposure"]
    result = evaluate_frame(shared, report([GROUP_DETECTORS[1]], subject="entity:other"))[0]
    assert result.tp == 0 and result.fn == 1
    duplicate = type(shared[0]).model_validate({**shared[0].model_dump(), "opportunity_id": "different.id"})
    with pytest.raises(ValueError, match="duplicate physical"):
        evaluate_frame([*shared, duplicate], report([]))


def test_complete_declared_inventory_has_unique_predeclared_frames():
    from pathlib import Path
    from tadr_benchmark.scenarios.families import load_family_scenarios
    scenarios = load_family_scenarios(Path(__file__).parents[1])
    assert len(scenarios) == 370
    for scenario in scenarios:
        labels = expectations_for(scenario)
        for variant in labels.normative:
            frame = alpha_opportunities(scenario, variant.variant_id, labels)
            assert len({o.opportunity_id for o in frame}) == len(frame)
            positive = {(o.check_id, o.subject) for o in frame if o.track == "normative" and o.positive}
            assert positive == {(f.check_id, f.subject) for f in variant.findings}
            physical = [(o.scenario_id, o.physical_defect_id, o.subject) for o in frame if o.track == "controlled_condition"]
            assert len(physical) == len(set(physical))

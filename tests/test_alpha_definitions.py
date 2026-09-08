"""Construction tests only: no target evaluation and no research-scale datasets."""

import ast
from collections import Counter
from pathlib import Path

import pytest

from tadr_benchmark.campaigns.loader import load_campaign, load_model
from tadr_benchmark.generators.tabular import injected_row, logical_row
from tadr_benchmark.scenarios.expectations import expectations_for, make_scenario, normative
from tadr_benchmark.scenarios.families import FamilyInventory, expand_families, load_family_scenarios
from tadr_benchmark.scenarios.ledger import physical_ledger
from tadr_benchmark.scenarios.recipe import (Recipe, block, bounded_selected, column_names,
                                            placement_mask, recipe_from_id, task_parameters)
from tadr_benchmark.serialization import canonical_bytes

ROOT = Path(__file__).parents[1]
SCENARIOS = load_family_scenarios(ROOT)
SMALL = [s for s in SCENARIOS if s.source_format == "csv" and s.row_count <= 10000 and not s.scenario_id.startswith("scale.")]


def test_exact_inventory_family_counts_and_normalized_id_conventions():
    manifest = load_campaign(ROOT / "campaigns/ALPHA_BENCHMARK_V1.yaml")
    ids = [s.scenario_id for s in SCENARIOS]
    assert len(ids) == len(set(ids)) == 370
    assert ids == sorted(manifest.scenario_ids)
    assert Counter(s.generator_parameters["family"] for s in SCENARIOS) == {
        "clean": 8, "parse": 24, "missing": 30, "duplicate": 36, "class": 24,
        "identifier": 16, "timestamp": 36, "split": 12, "group": 42, "inference": 20,
        "leak": 40, "negative": 6, "challenge": 2, "composite": 24, "sampling": 36, "scale": 14}
    for sid in ids:
        assert not sid.startswith("negative.lexical_paid.")
        if sid.startswith("leak.control.") and ".support" not in sid:
            assert ".n10000." in sid
    assert {s.scenario_version for s in SCENARIOS} == {"1.0"}
    assert all(s.seed is None and s.rng_algorithm is None for s in SCENARIOS)


def test_expansion_reordering_stable_and_duplicate_families_rejected():
    inventory = load_model(ROOT / "scenarios/families/ALPHA_BENCHMARK_V1.json", FamilyInventory)
    reversed_inventory = FamilyInventory.model_validate({**inventory.model_dump(), "families": list(reversed(inventory.families))})
    assert expand_families(reversed_inventory) == SCENARIOS
    duplicate = inventory.families[0].model_copy(update={"family_id": "overlapping"})
    with pytest.raises(ValueError, match="overlapping"):
        expand_families(FamilyInventory.model_validate({**inventory.model_dump(), "families": [*inventory.families, duplicate]}))


@pytest.mark.parametrize("scenario", SMALL, ids=lambda s: s.scenario_id)
def test_exact_small_construction_counts_and_physical_ledgers(scenario):
    r = Recipe.model_validate(scenario.generator_parameters)
    rows = [injected_row(r, i) for i in range(r.row_count)]
    names = column_names(r)
    assert len(rows) == scenario.row_count
    assert all(set(row) == set(names) for row in rows)
    assert len(names) == scenario.column_count
    unique_rows = len({tuple(row[name] for name in names) for row in rows})
    expected_excess = r.count if r.family == "duplicate" and r.case == "rows" else (
        500 if r.family == "composite" and r.case.startswith("duplicates_group") else 0)
    assert r.row_count-unique_rows == expected_excess
    for condition in physical_ledger(r).conditions:
        counts = condition.counts
        if "full.missing" in counts:
            q = counts["full.missing"]
            assert sum(row[condition.columns[0]] is None for row in rows) == q.numerator
            assert q.denominator == len(rows)
        if "full.parse_failures" in counts:
            column = condition.columns[0]
            q = counts["full.parse_failures"]
            assert sum(row[column] in {"bad", "2020-13-40"} for row in rows) == q.numerator
            assert sum(row[column] is not None for row in rows) == q.denominator
        if "full.distinct" in counts:
            assert len({row[condition.columns[0]] for row in rows}) == counts["full.distinct"].numerator
        if condition.condition_id == "key.excess_reuse":
            assert len(rows)-len({(row["entity_key"], row["event_key"]) for row in rows}) == counts["full.excess"].numerator
        if "full.repeated_participants" in counts:
            groups = Counter(row["entity_key"] for row in rows)
            assert sum(size for size in groups.values() if size > 1) == counts["full.repeated_participants"].numerator
        if "full.minority" in counts:
            labels = Counter(row["y"] for row in rows)
            assert (min(labels.values()) if len(labels) > 1 else 0) == counts["full.minority"].numerator
        if "full.valid_timestamps" in counts:
            from datetime import date
            valid = 0
            for row in rows:
                try:
                    date.fromisoformat(row.get("event_time"))
                    valid += 1
                except (ValueError, TypeError):
                    pass
            assert valid == counts["full.valid_timestamps"].numerator
        if "full.complete_pairs" in counts:
            assert sum(row["probe_x"] is not None and row["y"] is not None for row in rows) == counts["full.complete_pairs"].numerator
    assert rows[0] == injected_row(r, 0)
    assert rows[-1] == injected_row(r, r.row_count-1)


@pytest.mark.parametrize("stem,counts,severities", [
    ("parse.numeric.f", [99, 100, 101, 499, 500, 501, 1999, 2000, 2001],
     [None, "LOW", "LOW", "LOW", "MEDIUM", "MEDIUM", "MEDIUM", "HIGH", "HIGH"]),
    ("missing.feature.m", [999, 1000, 1001, 2999, 3000, 3001], [None, "MEDIUM", "MEDIUM", "MEDIUM", "HIGH", "HIGH"]),
    ("missing.target.m", [99, 100, 101], [None, "HIGH", "HIGH"]),
    ("duplicate.rows.e", [9, 10, 11, 99, 100, 101, 499, 500, 501],
     [None, "LOW", "LOW", "LOW", "MEDIUM", "MEDIUM", "MEDIUM", "HIGH", "HIGH"]),
    ("duplicate.keys.e", [9, 10, 11, 99, 100, 101], [None, "MEDIUM", "MEDIUM", "MEDIUM", "HIGH", "HIGH"]),
    ("class.binary.min", [199, 200, 201, 999, 1000, 1001], ["HIGH", "MEDIUM", "MEDIUM", "MEDIUM", None, None])])
def test_predeclared_boundary_triplets(stem, counts, severities):
    for count, severity in zip(counts, severities):
        result = normative(recipe_from_id(f"{stem}{count}.n10000.csv"))
        assert [f.severity for f in result.findings] == ([] if severity is None else [severity])


def test_clean_controls_and_specificity_challenges_have_disjoint_denominators():
    annotations = [expectations_for(s) for s in SCENARIOS]
    assert sum(a.primary_clean_control_eligible for a in annotations) == 8
    specificity = [a for a in annotations if any(c.interpretation == "specificity" for c in a.challenges)]
    assert len(specificity) == 8
    assert not any(a.primary_clean_control_eligible for a in specificity)
    paid = next(a for a in specificity if a.scenario_id == "challenge.lexical_paid.n10000.csv")
    assert paid.normative[0].findings[0].severity == "INFO"
    assert all(not a.normative[0].findings for a in annotations if a.primary_clean_control_eligible)


def test_support_guards_and_gates_are_explicit():
    for n, confidence, cap in [(49, 0.68, []), (50, 0.82, [60]), (200, 0.92, [60])]:
        expectation = normative(recipe_from_id(f"leak.control.support{n}.csv"))
        assert expectation.findings[0].confidence == confidence
        assert [g.cap for g in expectation.gates] == cap
    for n, expected in [(99, []), (100, ["MEDIUM"])]:
        assert [f.severity for f in normative(recipe_from_id(f"class.support.n{n}.min5.csv")).findings] == expected


def test_timestamp_triplets_gates_and_composite_suppression():
    for task, severe, degraded, cap in [("time_series", "CRITICAL", "HIGH", [50]), ("regression", "HIGH", "MEDIUM", [])]:
        for valid, expected in [(7999, severe), (8000, degraded), (8001, degraded),
                                (9499, degraded), (9500, None), (9501, None)]:
            result = normative(recipe_from_id(f"timestamp.{task}.valid{valid}.n10000.csv"))
            assert [f.severity for f in result.findings] == ([] if expected is None else [expected])
            assert [g.cap for g in result.gates] == (cap if valid < 8000 else [])
    random = normative(recipe_from_id("composite.duplicates_group_random.n10000.csv"))
    assert len(random.suppressions) == 1
    assert sum(f.check_id == "quality.duplicates" for f in random.findings) == 2
    grouped = normative(recipe_from_id("composite.duplicates_group_group.n10000.csv"))
    assert not grouped.suppressions and len(grouped.findings) == 2
    capped = normative(recipe_from_id("composite.quality_accumulation_k3.n10000.csv"))
    assert capped.expected_category_caps == {"quality": 40.0}


def test_inference_candidate_roles_and_all_four_tasks():
    for s in SCENARIOS:
        if not s.scenario_id.startswith("inference."):
            continue
        r = Recipe.model_validate(s.generator_parameters)
        task = task_parameters(r)
        excluded = {task["target_column"], task["timestamp_column"], task["group_column"], *task["id_columns"]}
        availability = task["inference_available_columns"]
        missing = [] if availability is None else [c for c in column_names(r) if c not in excluded and c not in availability]
        assert [f.subject for f in normative(r).findings] == ["column:"+c for c in missing]
        assert bool(normative(r).gates) == bool(missing)


def test_ground_truth_module_graph_has_no_target_or_adapter_dependencies():
    for directory in ("scenarios", "generators"):
        for path in (ROOT / "src/tadr_benchmark" / directory).glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    continue
                assert not any(name == "tadr" or name.startswith("tadr.") or "targets" in name for name in names)
    for s in SCENARIOS:
        annotation = expectations_for(s)
        assert annotation == expectations_for(s)
        assert "readiness_score" not in annotation.model_dump_json()
        assert "report" not in type(annotation).model_fields


def test_mutated_oracle_cannot_be_substituted_for_independent_labels():
    original = next(s for s in SCENARIOS if s.scenario_id == "missing.feature.m1000.n10000.csv")
    mutated = type(original).model_validate({**original.model_dump(), "expected_findings": []})
    with pytest.raises(ValueError, match="independent"):
        expectations_for(mutated)


def test_masks_reject_overlap_and_out_of_bounds():
    from tadr_benchmark.companions import RowMask
    for ranges in ([{"start": 0, "stop": 11}],
                   [{"start": 0, "stop": 10, "step": 2}, {"start": 4, "stop": 9, "step": 3}]):
        with pytest.raises(ValueError):
            RowMask(row_count=10, ranges=ranges)
    assert block(10, 0, 0).count == 0


@pytest.mark.parametrize("scenario", [s for s in SCENARIOS if s.scenario_id.startswith("sampling.")], ids=lambda s: s.scenario_id)
def test_sampling_placement_ledgers_without_materializing_the_corpus(scenario):
    r = Recipe.model_validate(scenario.generator_parameters)
    mask = placement_mask(r)
    assert mask.count == r.count
    # Counting mathematical positions is not generation of a 300k-row dataset.
    positions = sorted(i for span in mask.ranges for i in range(span.start, span.stop, span.step))
    assert len(set(positions)) == r.count
    expected_selected = 0 if r.placement == "gaps" else r.count if r.placement == "head" else 3*r.count//5
    assert sum(bounded_selected(i) for i in positions) == expected_selected
    assert mask.rank(positions[0]) == 0 and mask.rank(positions[-1]) == r.count-1
    ledger = physical_ledger(r).conditions[0]
    assert ledger.counts["P.placed"].numerator == expected_selected
    for i in (positions[0], positions[-1]):
        row = injected_row(r, i)
        if r.case == "missingness":
            assert row["signal_x"] is None
        elif r.case == "parse":
            assert row["signal_x"] == "bad"
        elif r.case.startswith("duplicate") or r.case == "group":
            source = injected_row(r, mask.rank(i))
            columns = column_names(r) if r.case == "duplicate_rows" else ["entity_key", "event_key"] if r.case == "duplicate_keys" else ["entity_key"]
            assert all(row[c] == source[c] for c in columns)
        elif r.case.startswith("class_"):
            assert row["y"] == "L1"
        elif r.case == "cardinality":
            assert row["probe_id"] == "probe_0"
        elif r.case == "leakage":
            assert row["probe_x"] == -500


def test_sampling_expected_contrasts_are_explicit():
    for family, placement, severity in [("duplicate_rows", "gaps", None), ("class_rare", "gaps", None),
        ("class_boundary", "middle", "MEDIUM"), ("cardinality", "head", None),
        ("group", "gaps", None), ("leakage", "head", None), ("leakage", "tail", "CRITICAL")]:
        result = normative(recipe_from_id(f"sampling.{family}.{placement}.n300000.pqstr"), "HEAD_STRIDE_V1")
        assert [f.severity for f in result.findings] == ([] if severity is None else [severity])


def test_scale_dimensions_and_native_types_without_dataset_generation():
    scale = [s for s in SCENARIOS if s.scenario_id.startswith("scale.")]
    assert len(scale) == 14
    assert sum(s.row_count for s in scale) == 9540000
    assert sum(s.row_count*s.column_count for s in scale) == 292400000
    for s in scale:
        r = Recipe.model_validate(s.generator_parameters)
        for i in (0, s.row_count-1):
            assert len(logical_row(r, i)) == s.column_count
        if r.representation == "pqnative":
            assert type(logical_row(r, 0)[0]) is int
            assert type(logical_row(r, 0)[5]) is bool

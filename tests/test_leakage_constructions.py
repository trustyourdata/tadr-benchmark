from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation

import pytest

from tadr_benchmark.generators.tabular import injected_row
from tadr_benchmark.scenarios.expectations import normative
from tadr_benchmark.scenarios.ledger import physical_ledger
from tadr_benchmark.scenarios.recipe import recipe_from_id


def equality_count(pairs):
    count = 0
    for left, right in pairs:
        if left is None or right is None or isinstance(left, bool) != isinstance(right, bool):
            continue
        try:
            count += Decimal(str(left)) == Decimal(str(right))
        except InvalidOperation:
            count += left == right
    return count


def joint_modal_count(pairs):
    forward, reverse = defaultdict(Counter), defaultdict(Counter)
    for x, y in pairs:
        forward[x][y] += 1
        reverse[y][x] += 1
    modes_x = {x: max(counts, key=lambda k: (counts[k], str(k))) for x, counts in forward.items()}
    modes_y = {y: max(counts, key=lambda k: (counts[k], str(k))) for y, counts in reverse.items()}
    return sum(modes_x[x] == y and modes_y[y] == x for x, y in pairs)


@pytest.mark.parametrize("case,expected", [
    ("equality.m9989.n10000", 9989), ("equality.m9990.n10000", 9990),
    ("equality.m9991.n10000", 9991), ("control.numeric_normalization.n10000", 10000),
    ("control.bool_numeric_mapping.n10000", 0)])
def test_direct_equality_count_and_numeric_normalization(case, expected):
    r = recipe_from_id("leak."+case+".csv")
    rows = [injected_row(r, i) for i in range(r.row_count)]
    assert equality_count([(row["probe_x"], row["y"]) for row in rows]) == expected


@pytest.mark.parametrize("case,expected", [
    ("mapping.r9989.n10000", 9989), ("mapping.r9990.n10000", 9990),
    ("mapping.r9991.n10000", 9991), ("mapping.r10000.n10000", 10000),
    ("control.bool_numeric_mapping.n10000", 10000), ("control.many_to_one.n10000", 5000),
    ("control.one_to_many.n10000", 5000), ("control.joint_mode_exceptions.n10000", 9980)])
def test_reciprocal_joint_mapping_counts_recounted_from_contingency(case, expected):
    r = recipe_from_id("leak."+case+".csv")
    rows = [injected_row(r, i) for i in range(r.row_count)]
    pairs = [(row["probe_x"], row["y"]) for row in rows]
    assert joint_modal_count(pairs) == expected
    assert physical_ledger(r).conditions[0].counts["full.mapping_matches"].numerator == expected
    if case.endswith("joint_mode_exceptions.n10000"):
        assert Counter(pairs) == {("A", "X"): 4990, ("B", "Y"): 4990, ("A", "Z"): 10, ("C", "Y"): 10}
        assert [f.check_id for f in normative(r).findings] == ["quality.class_imbalance"]


def test_allowlist_and_variability_are_labels_not_silently_changed_data():
    for case in ("allowlisted_copy", "constant_target", "zero_pairs"):
        r = recipe_from_id(f"leak.control.{case}.n10000.csv")
        assert not any(f.check_id == "leakage.target_direct" for f in normative(r).findings)
        ledger = physical_ledger(r).conditions[0]
        assert ledger.counts["full.complete_pairs"].numerator == (0 if case == "zero_pairs" else 10000)
        assert ledger.counts["target.variable"].numerator == (0 if case == "constant_target" else 1)

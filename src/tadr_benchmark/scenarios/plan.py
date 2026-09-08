"""Independent coverage obligations for the approved Alpha protocol.

Selective groups choose cells. This independent inventory prevents removal of
one required arm from being hidden by another arm covering the same scenario.
This validates metadata; it never executes a target.
"""

DETERMINISM_SMALL = frozenset({
    "clean.classification.n10000.csv", "clean.time_series.n10000.pqstr",
    "parse.numeric.f2001.n10000.csv", "missing.target.m100.n10000.pqstr",
    "duplicate.rows.e500.n10000.csv", "duplicate.keys.e100.n10000.pqstr",
    "group.random.r2000.n10000.csv", "inference.analytics.omit_one.n10000.pqstr",
    "leak.mapping.r9990.n10000.pqstr", "composite.timestamp_random.n10000.csv"})
DETERMINISM_SAMPLED = frozenset({"sampling.duplicate_rows.gaps.n300000.pqstr",
                                  "sampling.leakage.head.n300000.pqstr"})
CONTEXTS = frozenset({"standard", "hash_one", "hash_fortytwo", "timezone_berlin", "decimal_low", "decimal_high"})


def validate_alpha_cells(manifest, scenarios, runs) -> None:
    if {c.case_id for c in manifest.determinism_cases} != CONTEXTS:
        raise ValueError("Alpha determinism context inventory differs from approved protocol")
    expected = set()
    for scenario in scenarios:
        sid = scenario.scenario_id
        variants = ["full_reference", "HEAD_STRIDE_V1"] if sid.startswith("sampling.") else [
            "scale_default" if sid.startswith("scale.") else "full_reference"]
        for variant in variants:
            det = sid in DETERMINISM_SMALL or (sid in DETERMINISM_SAMPLED and variant == "HEAD_STRIDE_V1")
            contexts = CONTEXTS if det else {"standard"}
            large = sid == "scale.analytics.n5000000.w20.pqnative"
            scale = sid.startswith("scale.")
            measurements = 2 if det or large else 3 if scale else 1
            warmups = 1 if scale and not large else 0
            for context in contexts:
                for phase, count in (("warmup", warmups), ("measurement", measurements)):
                    expected.update((sid, variant, context, phase, i) for i in range(count))
    observed = {(r.scenario_id, r.analysis_variant, r.determinism_case_id, r.phase, r.repeat_index) for r in runs}
    if observed != expected:
        raise ValueError("uncovered or unexpected required Alpha execution cells")

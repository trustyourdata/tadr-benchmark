"""Physical labels derived from integer recipes, never from target output."""

from ..companions import CountRatio, PhysicalCondition, PhysicalLedger
from .recipe import Recipe, block, column_names, placement_mask, task_parameters


def physical_ledger(r: Recipe) -> PhysicalLedger:
    n, f, c, k = r.row_count, r.family, r.case, r.count
    conditions = []

    def add(name, columns, counts, masks=None, description=None):
        conditions.append(PhysicalCondition(condition_id=name, columns=columns,
                          counts={key: CountRatio(numerator=a, denominator=b) for key, (a, b) in counts.items()},
                          masks=masks or {}, description=description or name.replace(".", " ")))

    def missing(column, count, start=0):
        add("cell.missing."+column, [column], {"full.missing": (count, n)},
            {"nulls": block(n, start, count)})

    def parse(count, attempts=n, start=0, column="signal_x"):
        add("cell.numeric_corruption."+column, [column], {"full.parse_failures": (count, attempts)},
            {"malformed": block(n, start, count)})

    def groups(participants):
        add("entity.cross_split_exposure", ["entity_key"], {"full.repeated_participants": (participants, n)},
            {"participants": block(n, 0, participants)})

    def leak(equal, mapping, pairs=n, variable=True):
        masks = {}
        if c == "equality":
            masks = {"equal_pairs": block(n, 0, equal), "mismatches": block(n, equal, n-equal)}
        elif c == "mapping":
            masks = {"flipped_categories": block(n, 0, n-mapping), "joint_modal_pairs": block(n, n-mapping, mapping)}
        elif c == "many_to_one":
            masks = {"cell_"+name: block(n, j*2500, 2500) for j, name in enumerate(("A_L0", "B_L0", "C_L1", "D_L1"))}
        elif c == "one_to_many":
            masks = {"cell_A_L0": block(n, 0, 5000), "cell_A_L1": block(n, 5000, 5000)}
        elif c == "joint_mode_exceptions":
            masks = {"cell_A_X": block(n, 0, 4990), "cell_B_Y": block(n, 4990, 4990),
                     "cell_A_Z": block(n, 9980, 10), "cell_C_Y": block(n, 9990, 10)}
        else:
            masks = {"complete_pairs": block(n, 0, pairs)}
        add("feature.target_derived", ["probe_x", "y"],
            {"full.complete_pairs": (pairs, n), "full.equality_matches": (equal, pairs),
             "full.mapping_matches": (mapping, pairs), "target.variable": (int(variable), 1)}, masks)

    def timestamp(valid, nulls, malformed=0, absent=False):
        masks = {} if absent else {"valid": block(n, 0, valid), "nulls": block(n, valid, nulls),
                                   "malformed": block(n, valid+nulls, malformed)}
        add("timestamp.insufficient_validity", ["event_time"],
            {"full.valid_timestamps": (valid, n), "full.null_timestamps": (nulls, n),
             "full.malformed_timestamps": (malformed, n), "schema.timestamp_absent": (int(absent), 1)}, masks)

    if f == "parse":
        parse(k)
    if f == "missing":
        missing("y" if c == "target" else "signal_x", k)
    if f == "duplicate":
        add("row.excess_copy" if c == "rows" else "key.excess_reuse",
            column_names(r) if c == "rows" else ["entity_key", "event_key"],
            {"full.excess": (k, n), "full.distinct_rows": (n-k if c == "rows" else n, n)},
            {"sources": block(n, 0, k), "destinations": block(n, n-k, k)})
    if f == "class":
        add("label.rarity" if k else "label.collapsed_support", ["y"],
            {"full.minority": (k, n), "full.observed_classes": (2 if k else 1, 2)},
            {"minority": block(n, 0, k)})
    if f == "identifier" or f == "challenge":
        column = "paid" if f == "challenge" else "measurement" if c == "measurement" else "probe_id"
        unique = n if f == "challenge" else k
        add("identifier.cardinality", [column], {"full.distinct": (unique, n)},
            {"first_occurrences": block(n, 0, unique), "reused_first_value": block(n, unique, n-unique)})
    if f == "timestamp":
        timestamp(k, n-k if c != "absent" else 0, absent=c == "absent")
    if f == "split":
        timestamp(9499 if c == "reg_random_degraded" else n, 501 if c == "reg_random_degraded" else 0)
        if c == "ts_group":
            groups(n)
    if f == "group":
        groups(k)
    if f == "negative" and c == "analytics_entity":
        groups(2000)
    if f == "negative" and c == "declared_id":
        add("identifier.declared", ["probe_id"], {"full.distinct": (n, n)})
    if f == "leak":
        if c == "equality":
            leak(k, 0)
        elif c == "mapping":
            leak(0, k)
        elif c == "zero_pairs":
            leak(0, 0, 0)
            missing("probe_x", n)
        elif c == "constant_target":
            leak(n, 0, variable=False)
        elif c == "bool_numeric_mapping":
            leak(0, n)
        elif c in {"many_to_one", "one_to_many", "joint_mode_exceptions"}:
            leak(0, 9980 if c == "joint_mode_exceptions" else 5000)
            add("leakage.contingency", ["probe_x", "y"],
                {"forward_modal": (10000 if c == "many_to_one" else 5000 if c == "one_to_many" else 9990, n),
                 "reverse_modal": (5000 if c == "many_to_one" else 10000 if c == "one_to_many" else 9990, n)},
                description="Named contingency cells are defined independently in the versioned recipe and tested by recount.")
            if c == "joint_mode_exceptions":
                add("label.rarity", ["y"], {"full.minority": (10, n), "full.observed_classes": (3, 3)})
        else:
            leak(n, 0)
    if f == "composite":
        if c.startswith("duplicates_group"):
            add("row.excess_copy", column_names(r), {"full.excess": (500, n), "full.distinct_rows": (9500, n)},
                {"sources": block(n, 0, 500), "destinations": block(n, n-500, 500)})
            add("key.excess_reuse", ["entity_key", "event_key"], {"full.excess": (500, n)})
            add("entity.cross_split_exposure", ["entity_key"], {"full.repeated_participants": (2000, n)},
                {"copy_sources": block(n, 0, 500), "copy_destinations": block(n, n-500, 500),
                 "additional_pairs": block(n, 1000, 1000)})
        if c == "missing_parse":
            missing("signal_x", 2000)
            parse(400, 8000, 2000)
        if c in {"leak_missing", "leak_inference"}:
            leak(n, 0)
        if c in {"leak_missing", "inference_missing", "multicategory"}:
            missing("signal_z", 1000)
        if c.startswith("timestamp"):
            null = c == "timestamp_null_random"
            timestamp(7999, 2001 if null else 0, 0 if null else 2001)
            if not null:
                parse(2001, n, 7999, "event_time")
        if c.startswith("quality_accumulation"):
            for j in range(int(c[-1])):
                missing(f"q{j+1}", 3000, j*3000)
        if c == "multicategory":
            parse(500)
            groups(2000)
    if f == "sampling":
        mask = placement_mask(r)
        selected = 0 if r.placement == "gaps" else k if r.placement == "head" else 3*k//5
        counts = {"full.placed": (k, n), "P.placed": (selected, 200000)}
        names = {"missingness": ["signal_x"], "parse": ["signal_x"], "duplicate_rows": column_names(r),
                 "duplicate_keys": ["entity_key", "event_key"], "class_rare": ["y"], "class_boundary": ["y"],
                 "cardinality": ["probe_id"], "group": ["entity_key"], "leakage": ["probe_x", "y"]}[c]
        if c == "missingness":
            counts["full.missing"] = (k, n)
        elif c == "parse":
            counts["full.parse_failures"] = (k, n)
        elif c.startswith("duplicate"):
            counts.update({"full.excess": (k, n), "P.excess": (selected, 200000)})
        elif c.startswith("class_"):
            counts.update({"full.minority": (k, n), "P.minority": (selected, 200000),
                           "P.observed_classes": (2 if selected else 1, 2)})
        elif c == "cardinality":
            counts.update({"full.distinct": (n-k, n), "P.distinct": (200000-selected, 200000)})
        elif c == "group":
            counts.update({"full.repeated_participants": (2*k, n), "P.repeated_participants": (2*selected, 200000)})
        elif c == "leakage":
            counts.update({"full.equality_matches": (n-k, n), "P.equality_matches": (200000-selected, 200000)})
        masks = {"destinations": mask}
        if c in {"duplicate_rows", "duplicate_keys", "group"}:
            masks["sources"] = block(n, 0, k)
        add("sampling."+c, names, counts, masks)
    task = task_parameters(r)
    available = task["inference_available_columns"]
    if available is not None:
        excluded = {task["target_column"], task["timestamp_column"], task["group_column"], *task["id_columns"]}
        features = [c for c in column_names(r) if c not in excluded]
        missing_columns = [c for c in features if c not in available]
        add("feature.unavailable_at_prediction", missing_columns, {"schema.missing_features": (len(missing_columns), len(features))})
    if task["timestamp_column"] is not None or task["group_column"] is not None:
        add("split.intent", [], {}, description="Declared split="+task["split_strategy"]+"; roles are frozen in task_parameters.")
    return PhysicalLedger(scenario_id=r.scenario_id, row_count=n, column_names=column_names(r), conditions=conditions)

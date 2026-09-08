"""Construction recipes for the approved finite Alpha inventory, version 1.0.

Only integer positions and explicitly named task/column roles determine inputs.
No target package is imported here or by the generators and annotation modules.
"""

import re
from functools import lru_cache
from typing import Literal

from pydantic import model_validator

from ..companions import RowMask, RowRange
from ..models import Contract, Identifier, NonnegativeInt, PositiveInt, TaskType

COMPOSITES = {"duplicates_group_random", "duplicates_group_group", "missing_parse", "leak_missing",
              "timestamp_random", "inference_missing", "quality_accumulation_k1",
              "quality_accumulation_k2", "quality_accumulation_k3", "multicategory",
              "leak_inference", "timestamp_null_random"}
CONTROLS = {"allowlisted_copy", "constant_target", "zero_pairs", "support49", "support50", "support200",
            "numeric_normalization", "bool_numeric_mapping", "many_to_one", "one_to_many", "joint_mode_exceptions"}
SAMPLING = {"missingness": 30000, "parse": 3000, "duplicate_rows": 6000, "duplicate_keys": 6000,
            "class_rare": 3000, "class_boundary": 30000, "cardinality": 6000, "group": 15000, "leakage": 300}


class Recipe(Contract):
    recipe_version: Literal["1.0"] = "1.0"
    scenario_id: Identifier
    family: Literal["clean", "parse", "missing", "duplicate", "class", "identifier", "timestamp",
                    "split", "group", "inference", "leak", "negative", "challenge", "composite", "sampling", "scale"]
    case: str
    task: TaskType
    row_count: PositiveInt
    width: PositiveInt | None = None
    count: NonnegativeInt | None = None
    representation: Literal["csv", "pqstr", "pqnative"]
    placement: Literal["head", "middle", "tail", "gaps"] | None = None

    @model_validator(mode="after")
    def valid_count(self):
        if self.count is not None and self.count > self.row_count:
            raise ValueError("construction count exceeds row count")
        if self.family == "sampling" and (self.row_count != 300000 or self.placement is None):
            raise ValueError("sampling recipe requires the approved population and placement")
        return self


def recipe_from_id(scenario_id: str) -> Recipe:
    p = scenario_id.split(".")
    family, case, representation = p[0], p[1], p[-1]
    task, count, width, placement = "analytics", None, None, None
    n_tokens = [v for v in p if re.fullmatch(r"n[0-9]+", v)]
    n = int(n_tokens[0][1:]) if n_tokens else 10000
    if len(n_tokens) > 1:
        raise ValueError("ambiguous row count")
    if family in {"clean", "scale"}:
        task = case
        if family == "scale":
            width = int(p[3][1:])
    elif family == "parse":
        if case != "numeric":
            raise ValueError("unknown parse construction")
        count = int(p[2][1:])
    elif family in {"missing", "duplicate"}:
        allowed = {"feature", "target"} if family == "missing" else {"rows", "keys"}
        if case not in allowed:
            raise ValueError("unknown missing/duplicate construction")
        count = int(p[2][1:])
        task = "regression" if case == "target" else "analytics"
    elif family == "class":
        task = "classification"
        if case not in {"binary", "support"}:
            raise ValueError("unknown class construction")
        count = 5 if case == "support" else int(p[2][3:])
    elif family == "identifier":
        if case not in {"probe_id", "measurement", "support"}:
            raise ValueError("unknown identifier construction")
        count = n if case == "support" else int(p[2][1:])
    elif family == "timestamp":
        task = case
        case = "absent" if p[2] == "absent" else "valid"
        count = 0 if case == "absent" else int(p[2][5:])
    elif family == "split":
        if case not in {"ts_random", "ts_group", "reg_random_valid", "reg_time_valid",
                        "reg_random_degraded", "analytics_random_valid"}:
            raise ValueError("unknown split construction")
        task = "time_series" if case.startswith("ts_") else "regression" if case.startswith("reg_") else "analytics"
    elif family == "group":
        if case not in {"random", "time", "group"}:
            raise ValueError("unknown group split")
        task, count = "regression", int(p[2][1:])
        if count == 1:
            raise ValueError("one participant cannot form a repeated entity")
    elif family == "inference":
        task, case = case, p[2]
        if case not in {"null", "complete", "omit_one", "omit_two", "empty", "superset", "roles_only_excluded"}:
            raise ValueError("unknown inference construction")
    elif family == "leak":
        task = "classification" if case == "mapping" else "regression"
        if case in {"equality", "mapping"}:
            count = int(p[2][1:])
        elif case == "control" and p[2] in CONTROLS:
            case = p[2]
            if case.startswith("support"):
                n = int(case[7:])
            if case in {"many_to_one", "one_to_many", "joint_mode_exceptions"}:
                task = "classification"
        else:
            raise ValueError("unknown leakage construction")
    elif family == "negative":
        if case not in {"analytics_entity", "supervised_target_omitted", "declared_id"}:
            raise ValueError("unknown negative control")
        task = "classification" if case == "supervised_target_omitted" else "analytics"
    elif family == "challenge":
        if case != "lexical_paid":
            raise ValueError("unknown specificity challenge")
    elif family == "composite":
        if case not in COMPOSITES:
            raise ValueError("unknown composite")
        if case.startswith("timestamp"):
            task = "time_series"
        elif case.startswith("duplicates_group") or case in {"leak_missing", "leak_inference", "multicategory"}:
            task = "regression"
    elif family == "sampling":
        if case not in SAMPLING:
            raise ValueError("unknown sampling family")
        placement, count = p[2], SAMPLING[case]
        task = "classification" if case.startswith("class_") else "regression" if case in {"group", "leakage"} else "analytics"
    else:
        raise ValueError("unknown scenario family")
    return Recipe(scenario_id=scenario_id, family=family, case=case, task=task, row_count=n,
                  count=count, width=width, representation=representation, placement=placement)


def has_keys(r: Recipe) -> bool:
    return ((r.family == "duplicate" and r.case == "keys") or r.family == "group"
            or (r.family == "split" and r.case == "ts_group")
            or (r.family == "inference" and r.case == "roles_only_excluded")
            or (r.family == "negative" and r.case == "analytics_entity")
            or (r.family == "sampling" and r.case in {"duplicate_keys", "group"})
            or (r.family == "composite" and (r.case.startswith("duplicates_group") or r.case == "multicategory")))


@lru_cache(maxsize=512)
def column_names(r: Recipe) -> list[str]:
    omitted = r.family == "negative" and r.case == "supervised_target_omitted"
    names = ["coord_a", "coord_b", "coord_c", "signal_x", "signal_z", "flag", "segment",
             "event_time" if r.task == "analytics" or omitted else "y"]
    if r.task == "time_series" or r.family in {"timestamp", "split"}:
        if "event_time" not in names:
            names.append("event_time")
    if r.family == "timestamp" and r.case == "absent":
        names.remove("event_time")
    if has_keys(r):
        names += ["entity_key", "event_key"]
    if r.family == "identifier":
        names.append("measurement" if r.case == "measurement" else "probe_id")
    if r.family == "challenge":
        names.append("paid")
    if r.family == "negative" and r.case == "declared_id":
        names.append("probe_id")
    if r.family == "leak" or (r.family == "sampling" and r.case == "leakage") or (
            r.family == "composite" and r.case in {"leak_missing", "leak_inference"}):
        names.append("probe_x")
    if r.family == "sampling" and r.case == "cardinality":
        names.append("probe_id")
    if r.family == "composite" and r.case.startswith("quality_accumulation"):
        names += ["q1", "q2", "q3"]
    if r.width is not None:
        if r.width < len(names):
            raise ValueError("scale width is smaller than base schema")
        names += [f"aux_{i:03d}" for i in range(r.width-len(names))]
    return names


def task_parameters(r: Recipe) -> dict:
    p = dict(target_column=None if r.task == "analytics" else "y", timestamp_column=None,
             group_column=None, id_columns=[], split_strategy="time" if r.task == "time_series" else "random",
             inference_available_columns=None, allowed_leakage_columns=[], sensitive_columns=[],
             prediction_horizon=None, scoring_overrides=None)
    if r.task == "time_series" or r.family in {"timestamp", "split"}:
        p["timestamp_column"] = "event_time"
    if r.family == "timestamp":
        p["split_strategy"] = "time"
    if has_keys(r):
        p["id_columns"] = ["entity_key", "event_key"]
    group_role = (r.family == "group" or (r.family == "sampling" and r.case == "group")
                  or (r.family == "composite" and (r.case.startswith("duplicates_group") or r.case == "multicategory"))
                  or (r.family == "negative" and r.case == "analytics_entity")
                  or (r.family == "split" and r.case == "ts_group")
                  or (r.family == "inference" and r.case == "roles_only_excluded"))
    if group_role:
        p["group_column"] = "entity_key"
    if r.family == "group":
        p["split_strategy"] = r.case
    if r.family == "split":
        p["split_strategy"] = "group" if r.case == "ts_group" else "time" if r.case == "reg_time_valid" else "random"
    if r.family == "negative":
        if r.case == "supervised_target_omitted":
            p["target_column"] = None
        if r.case == "declared_id":
            p["id_columns"] = ["probe_id"]
    if r.family == "composite":
        if r.case == "duplicates_group_group":
            p["split_strategy"] = "group"
        if r.case.startswith("timestamp"):
            p["split_strategy"] = "random"
    if r.family == "leak" and r.case == "allowlisted_copy":
        p["allowed_leakage_columns"] = ["probe_x"]
    if r.family == "inference" and r.case == "roles_only_excluded":
        p["timestamp_column"] = "event_time"
    excluded = {p["target_column"], p["timestamp_column"], p["group_column"], *p["id_columns"]}
    candidates = [c for c in column_names(r) if c not in excluded]
    if r.family == "inference" and r.case != "null":
        missing = {"signal_x"} if r.case == "omit_one" else {"signal_x", "signal_z"} if r.case == "omit_two" else set()
        p["inference_available_columns"] = [] if r.case == "empty" else [c for c in candidates if c not in missing]
        if r.case == "superset":
            p["inference_available_columns"].append("deployment_aux")
    if r.family == "composite" and r.case in {"inference_missing", "leak_inference"}:
        omit = "probe_x" if r.case == "leak_inference" else "signal_x"
        p["inference_available_columns"] = [c for c in candidates if c != omit]
    return p


def block(n: int, start: int, count: int) -> RowMask:
    return RowMask(row_count=n, ranges=[] if not count else [RowRange(start=start, stop=start+count)])


@lru_cache(maxsize=64)
def placement_mask(r: Recipe) -> RowMask:
    n, length = r.row_count, r.count
    if r.family != "sampling" or length is None:
        raise ValueError("placement requires sampling recipe")
    if r.placement == "gaps":
        a, b = (length+1)//2, length//2
        return RowMask(row_count=n, ranges=[RowRange(start=50002, stop=50002+5*(a-1)+1, step=5),
                                            RowRange(start=50004, stop=50004+5*(b-1)+1, step=5)])
    start = 135000 if r.placement == "middle" else n-length if r.placement == "tail" else {
        "duplicate_rows": 12000, "duplicate_keys": 12000, "cardinality": 1, "group": 20000}.get(r.case, 0)
    return block(n, start, length)


def bounded_selected(index: int) -> bool:
    return index < 50000 or (index-50000) % 5 in {0, 1, 3}


def repeated_entity(index: int, participants: int) -> str:
    if index >= participants:
        return f"single_{index}"
    if participants % 2:
        return "repeat_0" if index < 3 else f"repeat_{1+(index-3)//2}"
    return f"repeat_{index//2}"

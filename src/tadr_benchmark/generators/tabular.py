"""Lazy deterministic base rows and Check Set A defect injection.

Row-addressable construction keeps scale specifications testable without
materializing research datasets. There is no target execution path here.
"""

from collections.abc import Iterator

from ..scenarios.recipe import (Recipe, column_names, has_keys, placement_mask,
                                repeated_entity)


def base_row(r: Recipe, index: int) -> dict:
    n, i = r.row_count, index
    small = n in {49, 50, 99, 100, 200}
    row = dict(coord_a=i % (10 if small else 1000),
               coord_b=i//10 if small else (i//1000) % 1000,
               coord_c=0 if small else (i//1000000) % 1000,
               signal_x=1000+i % 17, signal_z=2000+(i//17) % 19,
               flag=bool(i % 2), segment=f"g{(i//7) % 13}")
    names = column_names(r)
    if "y" in names:
        row["y"] = f"L{(i+i//1000) % 2}" if r.task == "classification" else 3000+i % 101
    if "event_time" in names:
        row["event_time"] = f"2020-01-{1+i % 28:02d}"
    if has_keys(r):
        row.update(entity_key=f"entity_{i}", event_key=f"event_{i}")
    for j, name in enumerate(c for c in names if c.startswith("aux_")):
        row[name] = 4000+100*j+((i*(2*j+1)+i//97) % 97)
    return row


def injected_row(r: Recipe, index: int) -> dict:
    n, f, c, k = r.row_count, r.family, r.case, r.count
    if not 0 <= index < n:
        raise IndexError("row index outside recipe")
    i = index
    mask = placement_mask(r) if f == "sampling" else None
    selected = mask.contains(index) if mask else False
    # Full-row copies happen before any column-level changes; destinations retain
    # every scalar of their source, including coordinates, labels and keys.
    if f == "duplicate" and c == "rows" and k and index >= n-k:
        i = index-(n-k)
    if f == "sampling" and c == "duplicate_rows" and selected:
        i = mask.rank(index)
    if f == "composite" and c.startswith("duplicates_group") and index >= n-500:
        i = index-(n-500)
    row = base_row(r, i)
    if f == "parse" and i < k:
        row["signal_x"] = "bad"
    if f == "missing" and i < k:
        row["y" if c == "target" else "signal_x"] = None
    if f == "duplicate" and c == "keys" and k and i >= n-k:
        row.update(entity_key=f"entity_{i-(n-k)}", event_key=f"event_{i-(n-k)}")
    if f == "class":
        row["y"] = "L1" if i < k else "L0"
    if f == "identifier":
        v = i if i < k else 0
        row["measurement" if c == "measurement" else "probe_id"] = 50000+v if c == "measurement" else f"probe_{v}"
    if f == "timestamp" and c != "absent" and i >= k:
        row["event_time"] = None
    if f == "split":
        if c == "reg_random_degraded" and i >= 9499:
            row["event_time"] = None
        if c == "ts_group":
            row["entity_key"] = f"group_{i % 10}"
    if f == "group":
        row["entity_key"] = repeated_entity(i, k)
    if f == "negative":
        if c == "analytics_entity":
            row["entity_key"] = repeated_entity(i, 2000)
        if c == "declared_id":
            row["probe_id"] = f"probe_{i}"
    if f == "challenge":
        row["paid"] = 50000+i
    if f == "leak":
        row["probe_x"] = row["y"]
        if c == "equality":
            row["probe_x"] = row["y"] if i < k else -500
        elif c == "mapping":
            bit = int(row["y"][-1])
            row["probe_x"] = ("A", "B")[1-bit if i < n-k else bit]
        elif c == "constant_target":
            row["y"] = row["probe_x"] = 3000
        elif c == "zero_pairs":
            row["probe_x"] = None
        elif c == "numeric_normalization":
            row["probe_x"] = f"{row['y']:08d}"
        elif c == "bool_numeric_mapping":
            row["y"], row["probe_x"], row["flag"] = i % 2, bool(i % 2), "neutral"
        elif c == "many_to_one":
            row["probe_x"], row["y"] = "ABCD"[i//2500], f"L{i//5000}"
        elif c == "one_to_many":
            row["probe_x"], row["y"] = "A", f"L{i//5000}"
        elif c == "joint_mode_exceptions":
            row["probe_x"], row["y"] = (("A", "X") if i < 4990 else ("B", "Y") if i < 9980
                                        else ("A", "Z") if i < 9990 else ("C", "Y"))
    if f == "composite":
        if c.startswith("duplicates_group") and 1000 <= i < 2000:
            row["entity_key"] = f"extra_{(i-1000)//2}"
        if c == "missing_parse":
            row["signal_x"] = None if i < 2000 else "bad" if i < 2400 else row["signal_x"]
        if c in {"leak_missing", "leak_inference"}:
            row["probe_x"] = row["y"]
        if c in {"leak_missing", "inference_missing", "multicategory"} and i < 1000:
            row["signal_z"] = None
        if c.startswith("timestamp") and i >= 7999:
            row["event_time"] = None if c == "timestamp_null_random" else "2020-13-40"
        if c.startswith("quality_accumulation"):
            active = int(c[-1])
            for j in range(3):
                row[f"q{j+1}"] = None if j < active and 3000*j <= i < 3000*(j+1) else 6000+j*100+i % 17
        if c == "multicategory":
            row["entity_key"] = repeated_entity(i, 2000)
            if i < 500:
                row["signal_x"] = "bad"
    if f == "sampling":
        if c == "missingness" and selected:
            row["signal_x"] = None
        if c == "parse" and selected:
            row["signal_x"] = "bad"
        if c == "duplicate_keys" and selected:
            source = mask.rank(index)
            row.update(entity_key=f"entity_{source}", event_key=f"event_{source}")
        if c.startswith("class_"):
            row["y"] = "L1" if selected else "L0"
        if c == "cardinality":
            row["probe_id"] = f"probe_{0 if selected else i}"
        if c == "group" and selected:
            row["entity_key"] = f"entity_{mask.rank(index)}"
        if c == "leakage":
            row["probe_x"] = -500 if selected else row["y"]
    return row


def logical_row(r: Recipe, index: int) -> list:
    row = injected_row(r, index)
    values = [row[name] for name in column_names(r)]
    if r.representation == "pqnative":
        return values
    return [None if v is None else "true" if v is True else "false" if v is False else str(v) for v in values]


def iter_rows(r: Recipe) -> Iterator[list]:
    for index in range(r.row_count):
        yield logical_row(r, index)

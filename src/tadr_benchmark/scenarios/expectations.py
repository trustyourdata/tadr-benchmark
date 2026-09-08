"""Independently authored pinned-Alpha contract and challenge annotations.

The integer boundaries below are the approved experimental labels. They are
not imported check implementations, fitted scores or observed target output.
"""

from ..companions import (GateExpectation, NormativeFinding, ResearchChallenge,
                          ScenarioExpectations, SuppressionExpectation, VariantExpectations)
from ..models import DefectSpec, FindingExpectation, ScenarioSpec
from ..serialization import canonical_bytes, sha256
from .ledger import physical_ledger
from .recipe import Recipe, column_names, recipe_from_id, task_parameters

CHECKS = ("schema.datetime_unparseable", "schema.id_like_high_cardinality", "schema.parse_failures",
          "quality.high_missingness", "quality.duplicates", "quality.class_imbalance",
          "split.time_series_requires_time_split", "split.group_split_recommended", "split.group_leakage_risk",
          "inference.missing_at_inference", "leakage.target_direct")


def normative(r: Recipe, variant_id: str = "full_reference") -> VariantExpectations:
    n, f, c, k = r.row_count, r.family, r.case, r.count
    findings, gates, suppressions = [], [], []

    def finding(check, subject, severity, population="P", confidence=None):
        findings.append(NormativeFinding(check_id=check, subject=subject, severity=severity,
                                        population=population, confidence=confidence))

    def gate(kind, cap):
        if not any(g.kind == kind for g in gates):
            gates.append(GateExpectation(kind=kind, cap=cap))

    def missing(column, count):
        is_target = column == "y"
        if count*100 >= n*(1 if is_target else 10):
            finding("quality.high_missingness", "column:"+column,
                    "HIGH" if is_target or count*100 >= 30*n else "MEDIUM", "full")

    def parse(count, attempts=n, column="signal_x", eligible=True):
        if eligible and attempts and count*100 >= attempts:
            severity = "HIGH" if count*100 >= attempts*20 else "MEDIUM" if count*100 >= attempts*5 else "LOW"
            finding("schema.parse_failures", "column:"+column, severity, "full")

    def duplicate(excess, denominator=n, keys=False):
        if excess*1000 >= denominator:
            severity = ("HIGH" if excess*100 >= denominator else "MEDIUM") if keys else (
                "HIGH" if excess*100 >= denominator*5 else "MEDIUM" if excess*100 >= denominator else "LOW")
            finding("quality.duplicates", "entity:entity_key|event_key" if keys else "dataset", severity)

    def imbalance(minority, denominator=n):
        if denominator >= 100 and minority > 0 and minority*10 < denominator:
            finding("quality.class_imbalance", "column:y", "HIGH" if minority*50 < denominator else "MEDIUM")

    def identifier(unique, denominator=n, column="probe_id", info=False):
        if denominator >= 100 and unique*100 >= denominator*98:
            finding("schema.id_like_high_cardinality", "column:"+column, "INFO" if info else "LOW")

    def timestamp(valid):
        if valid*100 < n*95:
            hard = valid*100 < n*80
            ts = r.task == "time_series"
            finding("schema.datetime_unparseable", "column:event_time",
                    ("CRITICAL" if hard else "HIGH") if ts else ("HIGH" if hard else "MEDIUM"), "full")
            if ts and hard:
                gate("invalid_timestamp", 50)

    def groups(participants, denominator=n):
        split = task_parameters(r)["split_strategy"]
        if r.task == "analytics" or split == "group" or participants*100 < denominator*5:
            return
        if split == "random" and participants*5 >= denominator:
            finding("split.group_leakage_risk", "entity:entity_key", "HIGH")
            suppressions.append(SuppressionExpectation(winner="split.group_leakage_risk",
                                 loser="split.group_split_recommended", subject="entity:entity_key"))
        else:
            finding("split.group_split_recommended", "entity:entity_key",
                    "HIGH" if participants*5 >= denominator else "MEDIUM")

    def leak(matches, denominator=n, eligible=True, confidence=None):
        if eligible and denominator and matches*1000 >= denominator*999:
            finding("leakage.target_direct", "column:probe_x", "CRITICAL", confidence=confidence)
            if confidence is None or confidence >= 0.70:
                gate("direct_leakage", 60)

    if f == "parse":
        parse(k, eligible=k <= 4000)
    elif f == "missing":
        missing("y" if c == "target" else "signal_x", k)
    elif f == "duplicate":
        duplicate(k, keys=c == "keys")
    elif f == "class":
        imbalance(k)
    elif f == "identifier":
        identifier(k, column="measurement" if c == "measurement" else "probe_id", info=c == "measurement")
    elif f == "challenge":
        identifier(n, column="paid", info=True)
    elif f == "timestamp":
        timestamp(k)
    elif f == "split":
        if c == "reg_random_degraded":
            timestamp(9499)
        if c in {"ts_random", "ts_group", "reg_random_valid"}:
            finding("split.time_series_requires_time_split", "dataset", "HIGH" if c.startswith("ts_") else "MEDIUM", "metadata")
    elif f == "group":
        groups(k)
    elif f == "leak":
        if c in {"equality", "mapping"}:
            leak(k)
        elif c.startswith("support"):
            leak(n, confidence={49: 0.68, 50: 0.82, 200: 0.92}[n])
        elif c in {"numeric_normalization", "bool_numeric_mapping"}:
            leak(n)
        elif c == "zero_pairs":
            missing("probe_x", n)
        elif c == "joint_mode_exceptions":
            imbalance(10)
    elif f == "composite":
        if c.startswith("duplicates_group"):
            duplicate(500)
            duplicate(500, keys=True)
            groups(2000)
        if c == "missing_parse":
            missing("signal_x", 2000)
            parse(400, 8000)
        if c in {"leak_missing", "leak_inference"}:
            leak(n)
        if c in {"leak_missing", "inference_missing", "multicategory"}:
            missing("signal_z", 1000)
        if c.startswith("timestamp"):
            timestamp(7999)
            finding("split.time_series_requires_time_split", "dataset", "HIGH", "metadata")
            if c == "timestamp_random":
                parse(2001, column="event_time")
        if c.startswith("quality_accumulation"):
            for j in range(int(c[-1])):
                missing(f"q{j+1}", 3000)
        if c == "multicategory":
            groups(2000)
            parse(500)
    elif f == "sampling":
        sampled = variant_id == "HEAD_STRIDE_V1"
        selected = 0 if r.placement == "gaps" else k if r.placement == "head" else 3*k//5
        denominator = 200000 if sampled else n
        amount = selected if sampled else k
        if c == "missingness":
            missing("signal_x", k)
        elif c == "parse":
            parse(k)
        elif c in {"duplicate_rows", "duplicate_keys"}:
            duplicate(amount, denominator, keys=c == "duplicate_keys")
        elif c.startswith("class_"):
            imbalance(amount, denominator)
        elif c == "cardinality":
            identifier(denominator-amount, denominator)
        elif c == "group":
            groups(2*amount, denominator)
        elif c == "leakage":
            leak(denominator-amount, denominator)
    task = task_parameters(r)
    if task["inference_available_columns"] is not None:
        excluded = {task["target_column"], task["timestamp_column"], task["group_column"], *task["id_columns"]}
        for column in column_names(r):
            if column not in excluded and column not in task["inference_available_columns"]:
                finding("inference.missing_at_inference", "column:"+column, "CRITICAL", "metadata")
                gate("missing_at_inference", 70)
    return VariantExpectations(variant_id=variant_id, findings=findings,
                               absent_check_ids=sorted(set(CHECKS)-{f.check_id for f in findings}),
                               gates=gates, suppressions=suppressions,
                               expected_category_caps={"quality": 40.0} if f == "composite" and c == "quality_accumulation_k3" else {})


def challenges(r: Recipe) -> list[ResearchChallenge]:
    rows = []
    def add(name, interpretation, present, description):
        rows.append(ResearchChallenge(challenge_id=name, interpretation=interpretation,
                                      condition_present=present, description=description))
    if r.family == "challenge" or (r.family == "identifier" and r.case == "measurement"):
        add("informational_specificity", "specificity", False,
            "Legitimate numeric measurement; expected INFO is shown as contract conformance and assessed separately for usefulness. Excluded from primary clean-control FP denominator.")
    if r.family == "parse" and r.count == 6000:
        add("numeric_dominance_loss", "sensitivity", True, "Physical numeric corruption remains when expected numeric type is lost.")
    if r.family == "class" and r.count == 0:
        add("collapsed_target_support", "eligibility", True, "Single-class collapse is a physical limitation despite normative no-Finding.")
    if r.family == "leak" and r.case in {"many_to_one", "joint_mode_exceptions"}:
        add("nonreciprocal_target_encoding", "sensitivity", True, "Target-derived encoding does not meet pinned reciprocal direct-leakage predicate.")
    if r.family == "leak" and r.case == "allowlisted_copy":
        add("allowlisted_target_copy", "policy_control", True, "Explicit policy exclusion; no universal safety interpretation.")
    if r.family == "sampling":
        add("deterministic_placement", "sensitivity", True, "Deliberate placement can alter P support and eligibility; full-scan counts retain their population.")
    if r.family in {"parse", "missing", "duplicate", "class", "identifier", "group", "leak"}:
        if r.count and not normative(r).findings and not rows:
            add("subthreshold_or_support", "eligibility", True, "Nonzero engineered condition; absence is evaluated separately from contract conformance.")
    return rows


def make_scenario(r: Recipe) -> ScenarioSpec:
    expected = normative(r, "scale_default" if r.family == "scale" else "full_reference")
    ledger = physical_ledger(r)
    return ScenarioSpec(scenario_id=r.scenario_id, scenario_version="1.0",
        description="Deterministic Alpha condition: "+r.scenario_id,
        task_type=r.task, task_parameters=task_parameters(r), row_count=r.row_count,
        column_count=len(column_names(r)), source_format="csv" if r.representation == "csv" else "parquet",
        generator="alpha.tabular", generator_version="1.0", generator_parameters=r.model_dump(mode="json"),
        rng_algorithm=None, seed=None,
        defects=[DefectSpec(defect_id=c.condition_id, injector="alpha.check_set_a", injector_version="1.0",
                            parameters=c.model_dump(mode="json"), affected_columns=c.columns)
                 for c in ledger.conditions],
        tags=[r.family, r.representation, "construction", "primary_clean_control" if r.family == "clean"
              else "specificity_challenge" if any(c.interpretation == "specificity" for c in challenges(r)) else "experimental_condition"],
        expected_findings=[FindingExpectation(id_pattern=f.check_id+"::*", subject=f.subject) for f in expected.findings],
        expected_absent_findings=[FindingExpectation(id_pattern=c+"::*") for c in expected.absent_check_ids],
        expected_affected_columns=sorted({column for c in ledger.conditions for column in c.columns}),
        expected_gate_behavior="present" if expected.gates else "none",
        rationale="Independent version 1.0 construction and pinned-Alpha contract labels; no observed target output. Variant-specific labels are in the typed expectations companion.")


def expectations_for(scenario: ScenarioSpec) -> ScenarioExpectations:
    r = Recipe.model_validate(scenario.generator_parameters)
    if make_scenario(r) != scenario or recipe_from_id(scenario.scenario_id) != r:
        raise ValueError("scenario snapshot differs from independent family recipe")
    variants = ["full_reference", "HEAD_STRIDE_V1"] if r.family == "sampling" else [
        "scale_default" if r.family == "scale" else "full_reference"]
    return ScenarioExpectations(scenario_id=scenario.scenario_id, scenario_version=scenario.scenario_version,
        scenario_sha256=sha256(canonical_bytes(scenario)), physical=physical_ledger(r),
        normative=[normative(r, v) for v in variants], challenges=challenges(r),
        primary_clean_control_eligible=r.family == "clean")

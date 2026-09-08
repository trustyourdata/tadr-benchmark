"""Alpha opportunity frames authored from recipes and labels before observation."""

from ..companions import ScenarioExpectations
from ..models import ScenarioSpec
from ..scenarios.expectations import expectations_for
from ..scenarios.recipe import Recipe, column_names, task_parameters
from ..serialization import canonical_bytes, sha256
from .metrics import Opportunity

GROUP_DETECTORS = ["split.group_split_recommended", "split.group_leakage_risk"]


def alpha_opportunities(scenario: ScenarioSpec, variant_id: str,
                        labels: ScenarioExpectations | None = None) -> list[Opportunity]:
    independent = expectations_for(scenario)
    if labels is not None and labels != independent:
        raise ValueError("opportunity labels differ from independent definitions")
    labels = independent
    normative = next(v for v in labels.normative if v.variant_id == variant_id)
    recipe = Recipe.model_validate(scenario.generator_parameters)
    task, columns = task_parameters(recipe), column_names(recipe)
    roles = {task["target_column"], task["timestamp_column"], task["group_column"], *task["id_columns"]}
    features = [c for c in columns if c not in roles]
    stratum = "primary_clean" if labels.primary_clean_control_eligible else (
        "specificity_challenge" if any(c.interpretation == "specificity" for c in labels.challenges) else recipe.family)
    if recipe.row_count < 200:
        stratum += ".support_guard"
    if recipe.family == "class" and recipe.count == 0:
        stratum += ".collapsed_support"
    opportunities = []

    def add(track, check, subject, positive, *, defect=None, severity=None, detectors=None, scope=stratum):
        identity = [scenario.scenario_id, track, defect or check, subject]
        opportunities.append(Opportunity(opportunity_id="opportunity."+sha256(canonical_bytes(identity)),
            scenario_id=scenario.scenario_id, physical_defect_id=defect,
            track=track, check_id=check, subject=subject, positive=positive, severity=severity,
            stratum=scope, matching_check_ids=detectors or [check]))

    subjects: set[tuple[str, str]] = set()
    def declare(check, names):
        subjects.update((check, name) for name in names)
    numeric = [c for c in columns if c.startswith(("coord_", "signal_", "aux_", "q"))
               or c in {"measurement", "paid"} or c == "y" and recipe.task in {"regression", "time_series"}]
    declare("schema.parse_failures", ["column:"+c for c in numeric + (["event_time"] if "event_time" in columns else [])])
    if task["timestamp_column"] is not None:
        declare("schema.datetime_unparseable", ["column:"+task["timestamp_column"]])
        declare("split.time_series_requires_time_split", ["dataset"])
    for condition in labels.physical.conditions:
        if condition.condition_id.startswith("identifier."):
            declare("schema.id_like_high_cardinality", ["column:"+c for c in condition.columns])
    declare("quality.high_missingness", ["column:"+c for c in features + (
        [task["target_column"]] if task["target_column"] in columns else [])])
    declare("quality.duplicates", ["dataset"] + (["entity:"+"|".join(task["id_columns"])] if task["id_columns"] else []))
    if recipe.task == "classification" and task["target_column"] in columns:
        declare("quality.class_imbalance", ["column:"+task["target_column"]])
    entity = task["group_column"] or next(iter(task["id_columns"]), None)
    if entity:
        for check in GROUP_DETECTORS:
            declare(check, ["entity:"+entity])
    # Null availability and omitted-target cases remain separately visible guards.
    declare("inference.missing_at_inference", ["column:"+c for c in features])
    if task["target_column"] in columns:
        declare("leakage.target_direct", ["column:"+c for c in features])
    expected = {(f.check_id, f.subject): f for f in normative.findings}
    subjects.update(expected)
    for check, subject in sorted(subjects):
        label = expected.get((check, subject))
        scope = stratum
        if check == "inference.missing_at_inference" and task["inference_available_columns"] is None:
            scope += ".null_list_guard"
        if check in GROUP_DETECTORS and (recipe.task == "analytics" or task["split_strategy"] == "group"):
            scope += ".applicability_guard"
        add("normative", check, subject, label is not None, severity=label.severity if label else None, scope=scope)

    # Physical presence is determined by construction, independent of thresholds,
    # final warning selection, or the population that happened to be sampled.
    physical_keys = set()
    def physical(check, subject, present, defect, *, detectors=None, scope=stratum):
        key = (defect, subject)
        if key in physical_keys:
            raise ValueError("duplicate physical condition opportunity")
        physical_keys.add(key)
        add("controlled_condition", check, subject, present, defect=defect, detectors=detectors, scope=scope)
    for condition in labels.physical.conditions:
        defect, counts, cols = condition.condition_id, condition.counts, condition.columns
        def count(name):
            return counts[name].numerator
        if defect.startswith("cell.missing.") or defect == "sampling.missingness":
            physical("quality.high_missingness", "column:"+cols[0], count("full.missing") > 0, defect)
        elif defect.startswith("cell.numeric_corruption.") or defect == "sampling.parse":
            physical("schema.parse_failures", "column:"+cols[0], count("full.parse_failures") > 0, defect)
        elif defect in {"row.excess_copy", "key.excess_reuse", "sampling.duplicate_rows", "sampling.duplicate_keys"}:
            keyed = defect in {"key.excess_reuse", "sampling.duplicate_keys"}
            physical("quality.duplicates", "entity:"+"|".join(cols) if keyed else "dataset", count("full.excess") > 0, defect)
        elif defect.startswith("label.") or defect in {"sampling.class_rare", "sampling.class_boundary"}:
            physical("quality.class_imbalance", "column:y", count("full.minority")*2 != recipe.row_count, defect)
        elif defect.startswith("identifier.") or defect == "sampling.cardinality":
            legitimate = recipe.family == "challenge" or recipe.case == "measurement" or defect == "identifier.declared"
            physical("schema.id_like_high_cardinality", "column:"+cols[0], not legitimate, defect)
        elif defect == "timestamp.insufficient_validity":
            physical("schema.datetime_unparseable", "column:event_time", count("full.valid_timestamps") < recipe.row_count, defect)
        elif defect in {"entity.cross_split_exposure", "sampling.group"}:
            scope = stratum + (".applicability_guard" if recipe.task == "analytics" or task["split_strategy"] == "group" else "")
            # One (scenario, physical defect, entity subject), even if both mapped
            # warnings fire. Sampling uses the same physical condition identity.
            physical("entity.cross_split_exposure", "entity:"+cols[0], count("full.repeated_participants") > 0,
                     "entity.cross_split_exposure", detectors=GROUP_DETECTORS, scope=scope)
        elif defect in {"feature.target_derived", "sampling.leakage"}:
            present = (recipe.case not in {"constant_target", "zero_pairs", "one_to_many"})
            if recipe.case == "equality":
                present = count("full.equality_matches") > 0
            scope = stratum + (".policy_control" if recipe.case == "allowlisted_copy" else "")
            physical("leakage.target_direct", "column:probe_x", present, defect, scope=scope)
        elif defect == "feature.unavailable_at_prediction":
            for column in features:
                physical("inference.missing_at_inference", "column:"+column, column in cols, defect)
        elif defect == "split.intent" and task["timestamp_column"] is not None:
            physical("split.time_series_requires_time_split", "dataset",
                     recipe.task != "analytics" and task["split_strategy"] != "time", defect)
    # Fixed-frame negatives inherit the independently declared subject scopes,
    # never subjects discovered from a report. Existing condition opportunities
    # supersede the clean-background opportunity for their mapped checks/subject.
    covered = {(check, o.subject) for o in opportunities if o.track == "controlled_condition" for check in o.matching_check_ids}
    for check, subject in sorted(subjects - covered):
        # Group warnings share one physical entity opportunity, including controls.
        if check in GROUP_DETECTORS:
            if ("entity.cross_split_exposure", subject) not in physical_keys:
                physical("entity.cross_split_exposure", subject, False, "entity.cross_split_exposure", detectors=GROUP_DETECTORS)
        else:
            physical(check, subject, False, "background."+check)
    return sorted(opportunities, key=lambda o: o.opportunity_id)

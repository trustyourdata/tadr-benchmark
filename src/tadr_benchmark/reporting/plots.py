"""Matplotlib plots answer fixed experimental queries; absent data makes no plot."""

from collections import defaultdict
from dataclasses import dataclass
from io import BytesIO


@dataclass(frozen=True)
class PlotQuery:
    title: str
    x_label: str
    y_label: str
    points: tuple[tuple[str, object, float], ...]
    logarithmic_x: bool = False


def figure_queries(tables: dict[str, list[dict]]) -> dict[str, PlotQuery]:
    queries = {}
    detection = defaultdict(lambda: [0, 0, 0, 0])
    for row in tables["detection_by_check.csv"]:
        if row["severity_cutoff"] == "INFO":
            key = (row["track"], row["format"], row["analysis_variant"], row["stratum"], row["check_id"])
            for i, field in enumerate(("conditional_recall_numerator", "evaluable_positive_opportunities",
                                       "planned_positive_opportunities", "terminal_target_failures")):
                detection[key][i] += row[field]
    points = []
    for (track, fmt, variant, stratum, check), (detected, evaluable, planned, failures) in sorted(detection.items()):
        if not planned:
            continue
        series = track+" / "+fmt+" / "+variant
        label = f"{check} ({stratum}; {fmt}; positive opportunities {evaluable}/{planned} evaluable; failures={failures})"
        points.append((series+" / positive report coverage", label, evaluable/planned))
        if evaluable:
            points.append((series+" / conditional recall", label, detected/evaluable))
        if track == "controlled_condition":
            points.append((series+" / end-to-end detection yield", label, detected/planned))
    if points:
        queries["detection_by_check.svg"] = PlotQuery("Conditional detection, report coverage and end-to-end detection yield",
            "Check and planned/evaluable positive opportunity support", "Descriptive ratio", tuple(points))
    # Raw warning counts are shared by both evaluation tracks. Show them once,
    # at the INFO-inclusive cutoff, while retaining missing-report coverage.
    controls = [r for r in tables["clean_false_positives.csv"] if r["track"] == "normative" and r["severity_cutoff"] == "INFO"]
    if any(r["finding_count"] for r in controls):
        successful, planned, unavailable = (sum(r[k] for r in controls) for k in (
            "successful_reports", "planned_reports", "unevaluable_negative_opportunities"))
        queries["clean_false_positives.svg"] = PlotQuery(
            f"Warnings in successful reports; reports {successful}/{planned}; unevaluable negative opportunities={unavailable}",
            "Designed condition (primary controls and separate specificity challenges)", "Finding count",
            tuple((r["stratum"]+" / "+r["format"], r["scenario_id"], float(r["finding_count"]))
                  for r in controls if r["finding_count"] is not None))
    for family, name in (("missing", "missingness"), ("duplicate", "duplicates"), ("class", "class_imbalance"), ("leak", "leakage")):
        points = tuple((r["case"]+" / "+r["format"], r["count"], float(r["readiness_score"]))
                       for r in tables["score_sweeps.csv"] if r["family"] == family and r["count"] is not None)
        if points:
            queries[f"score_{name}.svg"] = PlotQuery("Readiness response across controlled "+name.replace("_", " "),
                "Declared construction count (see source table for denominator)", "Readiness score", points)
    for metric, filename, ylabel in (("runtime_median_seconds", "runtime_vs_rows.svg", "Median analyze wall time (s)"),
                                    ("peak_rss_median_bytes", "peak_rss_vs_rows.svg", "Median absolute sampled process-tree RSS (bytes)"),
                                    ("throughput_median_rows_per_second", "throughput_vs_rows.svg", "Median input rows / analyze second")):
        points = tuple((f"{r['task']} / {r['format']} / {r['column_count']} columns / {r['analysis_mode']}",
                        r["row_count"], float(r[metric])) for r in tables["scale_performance.csv"] if r[metric] is not None)
        if points:
            queries[filename] = PlotQuery("Scale cost by width, task and source representation", "Input rows", ylabel, points, True)
    for metric, filename, title, ylabel in (
            ("readiness_score_delta", "sampling_score_delta.svg", "Bounded-minus-full readiness response", "Readiness score delta"),
            ("finding_agreement", "sampling_finding_agreement.svg", "Bounded/full Finding agreement by placement", "Finding Jaccard")):
        points = tuple(("HEAD_STRIDE_V1 versus full", r["scenario_id"], float(r[metric])) for r in tables["sampling_fidelity.csv"])
        if points:
            queries[filename] = PlotQuery(title, "Controlled placement", ylabel, points)
    return queries


def render_svg(query: PlotQuery) -> bytes:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    if not query.points:
        raise ValueError("no observations for figure query")
    groups = defaultdict(list)
    for series, x, y in query.points:
        groups[series].append((x, y))
    categorical = any(isinstance(x, str) for _, x, _ in query.points)
    categories = sorted({x for _, x, _ in query.points}) if categorical else []
    with matplotlib.rc_context({"svg.hashsalt": "tadr-benchmark-1.0", "font.family": "DejaVu Sans"}):
        fig, ax = plt.subplots(figsize=(max(9, len(categories)*0.35), 6 if not categorical else 9))
        for name, points in sorted(groups.items()):
            points.sort(key=lambda p: p[0])
            x = [categories.index(p[0]) if categorical else p[0] for p in points]
            y = [p[1] for p in points]
            ax.plot(x, y, marker="o", linestyle="none" if categorical else "-", label=name)
        if categorical:
            ax.set_xticks(range(len(categories)), categories, rotation=70, ha="right")
        if query.logarithmic_x:
            ax.set_xscale("log")
        ax.set(title=query.title, xlabel=query.x_label, ylabel=query.y_label)
        ax.legend(fontsize="small")
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        output = BytesIO()
        fig.savefig(output, format="svg", metadata={"Date": None, "Creator": "tadr-benchmark"})
        plt.close(fig)
    return output.getvalue()


def build_figures(tables: dict[str, list[dict]]) -> dict[str, bytes]:
    return {name: render_svg(query) for name, query in sorted(figure_queries(tables).items())}

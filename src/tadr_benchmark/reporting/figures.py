from pathlib import Path

from ..models import CampaignSummary


def runtime_rows(summary: CampaignSummary) -> list[tuple[str, float]]:
    return [(f"{g.scenario_id}/{g.analysis_variant}/{g.environment_id[:8]}", g.runtime_median_seconds)
            for g in sorted(summary.groups, key=lambda g: (g.scenario_id, g.scenario_version,
                                                           g.analysis_variant, g.environment_id))]


def write_runtime_figure(summary: CampaignSummary, destination: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = runtime_rows(summary)
    if not rows:
        raise ValueError("figures require measured results")
    with matplotlib.rc_context({"svg.hashsalt": "tadr-benchmark-1.0", "font.family": "DejaVu Sans"}):
        figure, axis = plt.subplots(figsize=(9, max(3, len(rows) * 0.5)))
        axis.barh([row[0] for row in rows], [row[1] for row in rows])
        axis.set_xlabel("Median target analysis wall time (seconds)")
        figure.tight_layout()
        figure.savefig(destination, format="svg", metadata={"Date": None, "Creator": "tadr-benchmark"})
        plt.close(figure)

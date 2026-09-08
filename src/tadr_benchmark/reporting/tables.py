import csv
import io

from ..models import CampaignSummary, SummaryGroup


def summary_csv(summary: CampaignSummary) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(SummaryGroup.model_fields), lineterminator="\n")
    writer.writeheader()
    for group in sorted(summary.groups, key=lambda g: (g.scenario_id, g.scenario_version,
                                                      g.analysis_variant, g.environment_id)):
        writer.writerow(group.model_dump())
    return stream.getvalue()

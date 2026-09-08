"""Execution boundary reserved for the next, reviewed campaign implementation."""

from pathlib import Path
from typing import Protocol

from ..models import CampaignManifest, DatasetArtifact, RunResult, RunSpec
from ..companions import RunFailure
from ..targets.base import TargetAdapter


class InstrumentedExecutor(Protocol):
    """Execute in a fresh worker, enforce timeout, sample worker-tree RSS.

    Set determinism context before importing the target. Time only analyze;
    retain warmups separately. Infrastructure errors fail execution; missed
    Findings remain completed results. No implementation is enabled at bootstrap.
    """

    def execute(self, campaign: CampaignManifest, run: RunSpec,
                dataset: DatasetArtifact, target: TargetAdapter,
                repository: Path) -> RunResult | RunFailure: ...

from pathlib import Path
from typing import Protocol

from ..models import DatasetArtifact, DefectSpec, ScenarioSpec


class DatasetGenerator(Protocol):
    """Write working data with independent truth using explicit version/seed."""

    def generate(self, scenario: ScenarioSpec, repository: Path) -> DatasetArtifact: ...


class DefectInjector(Protocol):
    """Transform generated data; never consult target reports for ground truth."""

    def inject(self, dataset: DatasetArtifact, defect: DefectSpec,
               repository: Path) -> DatasetArtifact: ...

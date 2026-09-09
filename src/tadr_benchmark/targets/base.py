from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..models import TargetMetadata


@dataclass(frozen=True)
class TargetReport:
    """Original canonical bytes and unmodified JSON transport, not benchmark scoring."""

    canonical_bytes: bytes
    data: dict


class TargetAdapter(Protocol):
    def metadata(self) -> TargetMetadata: ...

    def analyze(self, dataset_path: Path, task: dict,
                constraints: dict | None = None) -> TargetReport: ...

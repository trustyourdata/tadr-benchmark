"""Separate provenance for processing immutable scientific observations."""

from typing import Literal

from ..models import Commit, Contract, Digest, EnvironmentInfo
from ..serialization import sha256
from .freeze import require_clean_revision


class ProcessingProvenance(Contract):
    processing_provenance_version: Literal["1.0"] = "1.0"
    execution_git_commit: Commit
    processing_git_commit: Commit
    execution_binding_sha256: Digest
    attempts_sha256: Digest
    processing_environment: EnvironmentInfo


def processing_provenance(root, manifest, execution_binding: bytes, attempts: bytes,
                          environment: EnvironmentInfo) -> ProcessingProvenance:
    """Capture a clean processing revision without resolving/replacing execution."""
    import json
    binding = json.loads(execution_binding)
    if binding["manifest"] != manifest.model_dump(mode="json"):
        raise ValueError("processing binding differs from execution manifest")
    return ProcessingProvenance(
        execution_git_commit=manifest.benchmark_git_commit,
        processing_git_commit=require_clean_revision(root),
        execution_binding_sha256=sha256(execution_binding),
        attempts_sha256=sha256(attempts), processing_environment=environment)

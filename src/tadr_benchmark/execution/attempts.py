"""Typed operational history; retries never create scientific multiplicity."""

from typing import Literal

from pydantic import model_validator

from ..companions import InstrumentationRecord, RunFailure
from ..models import Contract, Digest, Identifier, NonnegativeInt, RunResult, RunSpec, TargetMetadata
from ..serialization import canonical_bytes, sha256


class AttemptRecord(Contract):
    attempt_schema_version: Literal["1.0"] = "1.0"
    run_id: Identifier
    attempt_id: Identifier
    attempt_index: NonnegativeInt
    retry_of_attempt_id: Identifier | None
    execution_group_id: Identifier | None
    attempt_status: Literal["success", "target_failure", "infrastructure_failure"]
    failure_category: RunFailure.model_fields["failure_kind"].annotation | None
    safe_error_code: RunFailure.model_fields["error_code"].annotation | None
    infrastructure_resolution_status: Literal["not_applicable", "unresolved", "resolved"]
    resolution_code: Literal["startup_fixed", "context_fixed", "monitor_fixed",
                             "working_artifact_repaired", "harness_fixed"] | None = None
    selected_as_final_outcome: bool
    # The complete typed outcome binds all scenario, target, benchmark, dataset,
    # environment and context provenance, without repeating it inconsistently.
    outcome: RunResult | RunFailure
    outcome_sha256: Digest
    instrumentation: InstrumentationRecord | None

    @model_validator(mode="after")
    def consistent(self):
        outcome = self.outcome
        if self.run_id != outcome.run_id or self.execution_group_id != outcome.execution_group_id:
            raise ValueError("attempt/outcome identity mismatch")
        if self.attempt_id != attempt_id(self.run_id, self.attempt_index):
            raise ValueError("attempt identity differs from deterministic ordinal")
        if self.retry_of_attempt_id != (attempt_id(self.run_id, self.attempt_index-1)
                                       if self.attempt_index else None):
            raise ValueError("invalid retry lineage")
        if self.outcome_sha256 != sha256(canonical_bytes(outcome)):
            raise ValueError("attempt outcome checksum mismatch")
        infra = isinstance(outcome, RunFailure) and outcome.failure_kind == "infrastructure"
        status = "infrastructure_failure" if infra else (
            "target_failure" if isinstance(outcome, RunFailure) else "success")
        if self.attempt_status != status or self.selected_as_final_outcome == infra:
            raise ValueError("only first scientific terminal outcomes may be selected")
        if isinstance(outcome, RunFailure):
            if (self.failure_category != outcome.failure_kind or self.safe_error_code != outcome.error_code):
                raise ValueError("attempt failure metadata mismatch")
            if not infra and outcome.adjudication != "valid_target_outcome":
                raise ValueError("unadjudicated target outcome cannot be selected")
        elif self.failure_category is not None or self.safe_error_code is not None:
            raise ValueError("success cannot contain failure metadata")
        if infra:
            if self.infrastructure_resolution_status == "not_applicable":
                raise ValueError("infrastructure resolution must be explicit")
            if (self.infrastructure_resolution_status == "resolved") != (self.resolution_code is not None):
                raise ValueError("resolved infrastructure requires an adjudication code")
        elif self.infrastructure_resolution_status != "not_applicable" or self.resolution_code is not None:
            raise ValueError("scientific outcomes cannot be retried as infrastructure")
        if self.instrumentation and self.instrumentation.run_id != self.run_id:
            raise ValueError("attempt instrumentation identity mismatch")
        return self


def attempt_id(run_id: str, index: int) -> str:
    # Bounded identifier even when a RunSpec uses the full identifier length.
    return "attempt." + sha256(run_id.encode("utf-8"))[:32] + f".{index:06d}"


def make_attempt(outcome: RunResult | RunFailure, index: int = 0,
                 instrumentation: InstrumentationRecord | None = None, *,
                 resolution_code: str | None = None) -> AttemptRecord:
    failed = isinstance(outcome, RunFailure)
    infra = failed and outcome.failure_kind == "infrastructure"
    return AttemptRecord(
        run_id=outcome.run_id, attempt_id=attempt_id(outcome.run_id, index), attempt_index=index,
        retry_of_attempt_id=attempt_id(outcome.run_id, index-1) if index else None,
        execution_group_id=outcome.execution_group_id,
        attempt_status="infrastructure_failure" if infra else "target_failure" if failed else "success",
        failure_category=outcome.failure_kind if failed else None,
        safe_error_code=outcome.error_code if failed else None,
        infrastructure_resolution_status=("resolved" if resolution_code else "unresolved") if infra else "not_applicable",
        resolution_code=resolution_code, selected_as_final_outcome=not infra,
        outcome=outcome, outcome_sha256=sha256(canonical_bytes(outcome)), instrumentation=instrumentation)


def validate_attempts(specs: list[RunSpec], attempts: list[AttemptRecord],
                      runs: list[RunResult], failures: list[RunFailure], *, complete: bool = True) -> None:
    plan = {s.run_id: s for s in specs}
    if len(plan) != len(specs):
        raise ValueError("duplicate declared RunSpec")
    terminal = {o.run_id: o for o in [*runs, *failures]}
    if len(terminal) != len(runs) + len(failures):
        raise ValueError("multiple scientific terminal outcomes")
    history: dict[str, list[AttemptRecord]] = {}
    for attempt in attempts:
        if attempt.run_id not in plan:
            raise ValueError("attempt does not map to a declared RunSpec")
        if any(getattr(attempt.outcome, name) != getattr(plan[attempt.run_id], name)
               for name in RunSpec.model_fields):
            raise ValueError("attempt RunSpec provenance mismatch")
        history.setdefault(attempt.run_id, []).append(attempt)
    selected = {}
    binding_fields = ("benchmark_git_commit", "benchmark_package_version", "logical_dataset_sha256",
                      "source_file_sha256", "environment_id", *TargetMetadata.model_fields)
    for run_id, items in history.items():
        items.sort(key=lambda a: a.attempt_index)
        if [a.attempt_index for a in items] != list(range(len(items))):
            raise ValueError("nonsequential attempt indexes or orphan retry")
        for i, attempt in enumerate(items):
            if any(getattr(attempt.outcome, f) != getattr(items[0].outcome, f) for f in binding_fields):
                raise ValueError("retry provenance mismatch")
            if attempt.selected_as_final_outcome:
                if i != len(items)-1:
                    raise ValueError("retry after a scientific terminal outcome")
                selected[run_id] = attempt.outcome
            elif attempt.infrastructure_resolution_status != "resolved" and (complete or i != len(items)-1):
                raise ValueError("unresolved infrastructure failure")
    if selected != terminal:
        raise ValueError("selected attempts differ from runs/failures")
    if complete and set(selected) != set(plan):
        raise ValueError("every required RunSpec needs one selected outcome")


def attempt_bytes(attempts: list[AttemptRecord]) -> bytes:
    return b"".join(canonical_bytes(a) for a in sorted(attempts, key=lambda a: (a.run_id, a.attempt_index)))
